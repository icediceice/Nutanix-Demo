#!/usr/bin/env bash
set -euo pipefail

KUBECTL="${KUBECTL:-kubectl}"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

have() {
  command -v "$1" >/dev/null 2>&1
}

if ! have "$KUBECTL"; then
  fail "kubectl not found (set KUBECTL=... if needed)"
fi

echo "Cluster:"
"$KUBECTL" cluster-info >/dev/null
"$KUBECTL" config current-context

echo
echo "ArgoCD:"
if "$KUBECTL" -n argocd get application rx-demo >/dev/null 2>&1; then
  "$KUBECTL" -n argocd get application rx-demo -o wide
else
  warn "argocd/application rx-demo not found (run ./scripts/bootstrap-demo.sh)"
fi

echo
echo "Gatekeeper:"
if ! "$KUBECTL" get crd constrainttemplates.templates.gatekeeper.sh >/dev/null 2>&1; then
  warn "Gatekeeper CRDs not found (ConstraintTemplate). Policy constraints will not apply until Gatekeeper is installed."
fi

echo
echo "Istio:"
missing_istio=0
for crd in virtualservices.networking.istio.io destinationrules.networking.istio.io; do
  if ! "$KUBECTL" get crd "$crd" >/dev/null 2>&1; then
    warn "missing CRD: $crd"
    missing_istio=1
  fi
done
if [[ "$missing_istio" -eq 1 ]]; then
  warn "Istio CRDs missing: mesh scenarios will not apply until Istio is installed"
fi

echo
echo "KEDA (optional):"
if "$KUBECTL" get crd scaledobjects.keda.sh >/dev/null 2>&1; then
  echo "ScaledObject CRD: present"
else
  warn "ScaledObject CRD: missing (KEDA not detected). KEDA scenario branch will not work until KEDA is installed."
fi

echo
echo "Kommander (optional):"
if "$KUBECTL" get crd appdeployments.apps.kommander.d2iq.io >/dev/null 2>&1; then
  echo "AppDeployment CRD: present"
else
  warn "AppDeployment CRD: missing (Kommander not detected)"
fi

echo
echo "NKP Platform Apps (Kiali / Jaeger / Grafana):"
# Auto-detect workspace namespace.
WORKSPACE_NS="$("$KUBECTL" get ns -l workspaces.kommander.mesosphere.io/workspace-name \
  -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
if [[ -n "$WORKSPACE_NS" ]]; then
  echo "workspace namespace: ${WORKSPACE_NS}"
else
  WORKSPACE_NS="kommander-default-workspace"
  warn "could not auto-detect workspace namespace; checking '${WORKSPACE_NS}'"
fi

# Jaeger collector — needed for OTEL traces.
jaeger_ok=0
for svc_name in jaeger-jaeger-operator-jaeger-collector jaeger-collector; do
  for ns in istio-system "$WORKSPACE_NS"; do
    if "$KUBECTL" get svc "$svc_name" -n "$ns" >/dev/null 2>&1; then
      echo "Jaeger collector: ${svc_name}.${ns} (ready)"
      jaeger_ok=1
      break 2
    fi
  done
done
if [[ "$jaeger_ok" -eq 0 ]]; then
  warn "Jaeger collector service not found. Traces will be dropped. Deploy Jaeger via Kommander or check the workspace namespace."
fi

# Kiali — optional but expected for mesh visualization.
kiali_ok=0
for ns in "$WORKSPACE_NS" istio-system; do
  if "$KUBECTL" get svc kiali -n "$ns" >/dev/null 2>&1; then
    # Verify pod is actually running.
    kiali_ready="$("$KUBECTL" get pod -n "$ns" -l app.kubernetes.io/name=kiali -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || true)"
    if [[ "$kiali_ready" == "True" ]]; then
      echo "Kiali: ${ns} (ready)"
    else
      warn "Kiali service exists in ${ns} but pod is not Ready"
    fi
    kiali_ok=1
    break
  fi
done
if [[ "$kiali_ok" -eq 0 ]]; then
  warn "Kiali service not found. Mesh visualization will be unavailable. Deploy Kiali via Kommander."
fi

# Grafana.
grafana_ok=0
for svc_name in kube-prometheus-stack-grafana grafana; do
  if "$KUBECTL" get svc "$svc_name" -n "$WORKSPACE_NS" >/dev/null 2>&1; then
    echo "Grafana: ${svc_name}.${WORKSPACE_NS} (ready)"
    grafana_ok=1
    break
  fi
done
if [[ "$grafana_ok" -eq 0 ]]; then
  warn "Grafana service not found in ${WORKSPACE_NS}. Dashboards will be unavailable."
fi

echo
echo "Demo Namespaces:"
for ns in demo-app demo-ops; do
  if ! "$KUBECTL" get ns "$ns" >/dev/null 2>&1; then
    warn "missing namespace: $ns (platform will create it)"
  fi
done

echo
echo "Namespace cross-check (ArgoCD render vs cluster):"
if have kustomize; then
  KUSTOMIZE_CMD="kustomize build"
elif "$KUBECTL" kustomize clusters/rx-demo/argocd/root >/dev/null 2>&1; then
  KUSTOMIZE_CMD="$KUBECTL kustomize"
else
  warn "neither kustomize nor kubectl kustomize available — skipping namespace cross-check"
  KUSTOMIZE_CMD=""
fi

if [[ -n "${KUSTOMIZE_CMD:-}" ]]; then
  # Extract every unique namespace referenced in the rendered manifests.
  # Excludes lines inside 'name:' fields of kind: Namespace resources (we only
  # want the consumer side, not the definitions themselves).
  RENDER_FILE=$(mktemp /tmp/preflight-render.XXXXXX.yaml)
  $KUSTOMIZE_CMD clusters/rx-demo/argocd/root >"$RENDER_FILE" 2>/dev/null || {
    warn "kustomize build failed — skipping namespace cross-check"
    rm -f "$RENDER_FILE"
    KUSTOMIZE_CMD=""
  }
fi

if [[ -n "${KUSTOMIZE_CMD:-}" && -f "${RENDER_FILE:-/dev/null}" ]]; then
  ns_missing=0
  while IFS= read -r ns; do
    [[ -z "$ns" ]] && continue
    if ! "$KUBECTL" get namespace "$ns" >/dev/null 2>&1; then
      warn "ArgoCD render references namespace '$ns' — NOT FOUND in cluster"
      ns_missing=$((ns_missing + 1))
    fi
  done < <(
    python3 - "$RENDER_FILE" <<'PYEOF'
import sys, yaml
with open(sys.argv[1]) as f:
    docs = list(yaml.safe_load_all(f))
ns_set = set()
for doc in docs:
    if not isinstance(doc, dict):
        continue
    meta = doc.get("metadata") or {}
    if doc.get("kind") == "Namespace":
        continue  # skip definitions; we want consumers
    ns = meta.get("namespace", "")
    if ns:
        ns_set.add(ns)
for ns in sorted(ns_set):
    print(ns)
PYEOF
  )
  rm -f "$RENDER_FILE"
  if [[ "$ns_missing" -eq 0 ]]; then
    echo "all namespaces present in cluster"
  else
    warn "$ns_missing namespace(s) missing — ArgoCD will fail to sync until they exist"
  fi
fi

echo
echo "External Access:"
if "$KUBECTL" -n istio-helm-gateway-ns get svc istio-helm-ingressgateway >/dev/null 2>&1; then
  "$KUBECTL" -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide
else
  warn "istio-helm-gateway-ns/svc istio-helm-ingressgateway not found"
fi
if "$KUBECTL" -n demo-ops get svc demo-wall >/dev/null 2>&1; then
  "$KUBECTL" -n demo-ops get svc demo-wall -o wide
else
  warn "demo-ops/svc demo-wall not found (will appear after ArgoCD sync)"
fi

echo
echo "OK"

