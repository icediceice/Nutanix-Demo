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

