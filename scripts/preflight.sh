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

