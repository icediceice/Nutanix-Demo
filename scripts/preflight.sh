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
echo "Flux:"
if ! "$KUBECTL" -n flux-system get gitrepository nkp-rx-demo >/dev/null 2>&1; then
  warn "flux-system/gitrepository nkp-rx-demo not found (did you apply clusters/rx-demo/flux?)"
fi
if ! "$KUBECTL" -n flux-system get kustomization platform apps mesh ops-loadgen >/dev/null 2>&1; then
  warn "one or more Flux Kustomizations missing (platform/apps/mesh/ops-loadgen)"
fi

echo
echo "Gatekeeper:"
if ! "$KUBECTL" get crd constrainttemplates.templates.gatekeeper.sh >/dev/null 2>&1; then
  fail "Gatekeeper CRDs not found (ConstraintTemplate). Install Gatekeeper before applying platform/policy."
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
echo "Demo Namespaces:"
for ns in demo-app demo-ops; do
  if ! "$KUBECTL" get ns "$ns" >/dev/null 2>&1; then
    warn "missing namespace: $ns (platform will create it)"
  fi
done

echo
echo "Registry Secret:"
if "$KUBECTL" -n demo-app get secret ghcr-pull >/dev/null 2>&1; then
  echo "demo-app/secret ghcr-pull: present"
else
  warn "demo-app/secret ghcr-pull: missing (required if GHCR images are private)"
fi

echo
echo "OK"

