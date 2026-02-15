#!/usr/bin/env bash
set -euo pipefail

KUBECTL="${KUBECTL:-kubectl}"

KUBECONFIG_PATH=""
CONTEXT_NAME=""

usage() {
  cat <<'EOF'
Usage:
  ./scripts/print-access.sh [--kubeconfig PATH] [--context NAME]

Prints:
  - Kommander UI (if detected on this cluster kubeconfig)
  - ArgoCD UI + initial admin password command (if installed)
  - Demo app ingress URL (Istio LoadBalancer)
  - Demo Wall URL (LoadBalancer)
EOF
}

fail() { echo "FAIL: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) KUBECONFIG_PATH="${2:-}"; shift 2 ;;
    --context) CONTEXT_NAME="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown arg: $1 (use --help)" ;;
  esac
done

if ! have "$KUBECTL"; then
  fail "kubectl not found (set KUBECTL=... if needed)"
fi

kc() {
  local args=()
  if [[ -n "${KUBECONFIG_PATH}" ]]; then args+=(--kubeconfig "${KUBECONFIG_PATH}"); fi
  if [[ -n "${CONTEXT_NAME}" ]]; then args+=(--context "${CONTEXT_NAME}"); fi
  "$KUBECTL" "${args[@]}" "$@"
}

svc_lb() {
  local ns="$1" name="$2"
  local ip host
  ip="$(kc -n "$ns" get svc "$name" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  host="$(kc -n "$ns" get svc "$name" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
  if [[ -n "$ip" ]]; then echo "$ip"; return 0; fi
  if [[ -n "$host" ]]; then echo "$host"; return 0; fi
  return 1
}

ing_hosts() {
  local ns="$1"
  kc -n "$ns" get ingress -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.rules[*]}{.host}{" "}{end}{"\n"}{end}' 2>/dev/null || true
}

echo "Context:"
kc config current-context 2>/dev/null || true
echo

echo "Kommander UI (if present):"
if kc get ns kommander >/dev/null 2>&1; then
  # Common: Ingress in ns "kommander" with host like kommander.<domain>
  hosts="$(ing_hosts kommander | sed '/^$/d' || true)"
  if [[ -n "${hosts}" ]]; then
    echo "$hosts" | while IFS=$'\t' read -r name h; do
      echo "  ingress/${name} hosts: ${h}"
    done
  else
    # Some installs expose services; print any LB services that look like kommander.
    kc -n kommander get svc -o wide 2>/dev/null | awk 'NR==1 || $1 ~ /kommander|traefik|nginx|dex|kommander-ui/'
  fi
else
  echo "  Not detected on this kubeconfig (namespace kommander not found)."
  echo "  If Kommander runs on a separate management cluster, run this script against the management kubeconfig."
fi
echo

echo "ArgoCD UI (if present):"
if kc -n argocd get deploy argocd-server >/dev/null 2>&1; then
  if lb="$(svc_lb argocd argocd-server)"; then
    echo "  URL: https://${lb}/"
  else
    echo "  URL: (no LoadBalancer) use: kubectl -n argocd port-forward svc/argocd-server 8443:443"
    echo "       then open: https://localhost:8443/"
  fi
  echo "  Username: admin"
  echo "  Initial password:"
  echo "    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d && echo"
else
  echo "  Not installed (namespace argocd or deploy/argocd-server not found)."
fi
echo

echo "Demo app (Istio ingress):"
if kc -n istio-helm-gateway-ns get svc istio-helm-ingressgateway >/dev/null 2>&1; then
  if lb="$(svc_lb istio-helm-gateway-ns istio-helm-ingressgateway)"; then
    echo "  URL: http://${lb}/"
  else
    echo "  Ingress service exists but has no external address yet:"
    echo "    kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide"
  fi
else
  echo "  Not found: istio-helm-gateway-ns/svc istio-helm-ingressgateway"
fi
echo

echo "Demo Wall:"
if kc -n demo-ops get svc demo-wall >/dev/null 2>&1; then
  if lb="$(svc_lb demo-ops demo-wall)"; then
    echo "  URL: http://${lb}/"
    echo "  API: http://${lb}/api/status"
  else
    echo "  Service exists but has no external address yet:"
    echo "    kubectl -n demo-ops get svc demo-wall -o wide"
  fi
else
  echo "  Not found: demo-ops/svc demo-wall (wait for ArgoCD sync)"
fi

