#!/usr/bin/env bash
set -euo pipefail

KUBECTL="${KUBECTL:-kubectl}"

APP_NAME="${APP_NAME:-rx-demo}"
ARGO_NS="${ARGO_NS:-argocd}"
WORKSPACE_NS="${WORKSPACE_NS:-kommander-default-workspace}"

REPO_URL_DEFAULT="https://github.com/icediceice/Nutanix-Demo.git"
BRANCH_DEFAULT="scenario/load-off"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/bootstrap-demo.sh [--kubeconfig PATH] [--context NAME] [--branch scenario/*] [--repo URL]
                             [--workspace-namespace NS] [--skip-kommander-apps]

What it does:
  1) (Optional) Enables required Kommander apps (Istio/Kiali/Jaeger) via AppDeployment (no UI clicks).
  2) Installs ArgoCD (LoadBalancer service) from clusters/rx-demo/argocd/bootstrap.
  3) Creates ArgoCD AppProject + Application and points it at a scenario branch.
  4) Prints the URLs/commands to access ArgoCD, the Demo App, and Demo Wall.
EOF
}

fail() { echo "FAIL: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

KUBECONFIG_PATH=""
CONTEXT_NAME=""
REPO_URL="$REPO_URL_DEFAULT"
BRANCH="$BRANCH_DEFAULT"
SKIP_KOMMANDER_APPS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) KUBECONFIG_PATH="${2:-}"; shift 2 ;;
    --context) CONTEXT_NAME="${2:-}"; shift 2 ;;
    --repo) REPO_URL="${2:-}"; shift 2 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --workspace-namespace) WORKSPACE_NS="${2:-}"; shift 2 ;;
    --skip-kommander-apps) SKIP_KOMMANDER_APPS=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown arg: $1 (use --help)" ;;
  esac
done

if ! have "$KUBECTL"; then
  fail "kubectl not found (set KUBECTL=... if needed)"
fi

autodetect_kubeconfig() {
  # If user explicitly set --kubeconfig/--context, don't guess.
  if [[ -n "${KUBECONFIG_PATH}" || -n "${CONTEXT_NAME}" ]]; then
    return 0
  fi

  # Respect KUBECONFIG env var if it points to a readable file.
  if [[ -n "${KUBECONFIG:-}" ]]; then
    if [[ -f "${KUBECONFIG}" ]]; then
      KUBECONFIG_PATH="${KUBECONFIG}"
      return 0
    fi
    if [[ -d "${KUBECONFIG}" ]]; then
      warn "KUBECONFIG points to a directory: ${KUBECONFIG}"
    else
      warn "KUBECONFIG is set but not a file: ${KUBECONFIG}"
    fi
  fi

  # Default kubeconfig is ~/.kube/config. If it's a directory (common mistake), kubectl will fail.
  local default_kc="${HOME}/.kube/config"
  if [[ -f "${default_kc}" ]]; then
    return 0
  fi

  if [[ -d "${default_kc}" ]]; then
    warn "Detected invalid kubeconfig path: ${default_kc} is a directory."
  fi

  # Try to be fool-proof: if exactly one kubeconfig exists under auth/, use it.
  # This keeps the demo workflow consistent with the docs.
  local -a candidates=()
  if [[ -d "auth" ]]; then
    while IFS= read -r -d '' f; do
      candidates+=("$f")
    done < <(find auth -maxdepth 1 -type f \( -name "*.conf" -o -name "*.kubeconfig" -o -name "kubeconfig" \) -print0 2>/dev/null || true)
  fi

  if [[ "${#candidates[@]}" -eq 1 ]]; then
    KUBECONFIG_PATH="${candidates[0]}"
    warn "Using kubeconfig auto-detected at: ${KUBECONFIG_PATH}"
    return 0
  fi

  if [[ "${#candidates[@]}" -gt 1 ]]; then
    warn "Multiple kubeconfigs found under auth/:"
    for c in "${candidates[@]}"; do echo "  - ${c}" >&2; done
    fail "Please re-run with --kubeconfig auth/<cluster>.conf"
  fi

  fail "No kubeconfig selected. Re-run with --kubeconfig auth/<cluster>.conf (example: --kubeconfig auth/workload02.conf)"
}

kc() {
  local args=()
  if [[ -n "${KUBECONFIG_PATH}" ]]; then args+=(--kubeconfig "${KUBECONFIG_PATH}"); fi
  if [[ -n "${CONTEXT_NAME}" ]]; then args+=(--context "${CONTEXT_NAME}"); fi
  "$KUBECTL" "${args[@]}" "$@"
}

wait_for_crd() {
  local crd="$1"
  local timeout_s="${2:-600}"
  local start
  start="$(date +%s)"
  while true; do
    if kc get crd "$crd" >/dev/null 2>&1; then
      return 0
    fi
    if (( "$(date +%s)" - start > timeout_s )); then
      return 1
    fi
    sleep 2
  done
}

resolve_clusterapp() {
  local prefix="$1"
  # ClusterApp names are typically "<app>-<version>". Choose the highest version.
  local candidates
  candidates="$(kc get clusterapp -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -E "^${prefix}-" || true)"
  if [[ -z "$candidates" ]]; then
    return 1
  fi
  # Strip prefix and '-' to sort versions, then re-attach the name.
  # shellcheck disable=SC2016
  echo "$candidates" | awk -v p="${prefix}-" '{v=$0; sub(p,"",v); print v "\t" $0}' | sort -V | tail -n 1 | awk '{print $2}'
}

enable_kommander_apps() {
  if [[ "$SKIP_KOMMANDER_APPS" -eq 1 ]]; then
    warn "Skipping Kommander app enablement (--skip-kommander-apps)"
    return 0
  fi

  if ! kc get crd appdeployments.apps.kommander.d2iq.io >/dev/null 2>&1; then
    warn "Kommander AppDeployment CRD not found; skipping Kommander app enablement"
    return 0
  fi
  if ! kc get crd clusterapps.apps.kommander.d2iq.io >/dev/null 2>&1; then
    warn "Kommander ClusterApp CRD not found; skipping Kommander app enablement"
    return 0
  fi

  kc get ns "$WORKSPACE_NS" >/dev/null 2>&1 || kc create ns "$WORKSPACE_NS" >/dev/null

  local istio_app kiali_app jaeger_app
  istio_app="$(resolve_clusterapp "istio-helm" || true)"
  kiali_app="$(resolve_clusterapp "kiali" || true)"
  jaeger_app="$(resolve_clusterapp "jaeger" || true)"

  if [[ -z "$istio_app" || -z "$kiali_app" || -z "$jaeger_app" ]]; then
    warn "Could not resolve required ClusterApps (istio-helm/kiali/jaeger)."
    warn "Check: kubectl get clusterapp | grep -E '^(istio-helm|kiali|jaeger)-'"
    return 0
  fi

  cat <<EOF | kc apply -f - >/dev/null
apiVersion: apps.kommander.d2iq.io/v1alpha3
kind: AppDeployment
metadata:
  name: istio-helm
  namespace: ${WORKSPACE_NS}
spec:
  appRef:
    kind: ClusterApp
    name: ${istio_app}
---
apiVersion: apps.kommander.d2iq.io/v1alpha3
kind: AppDeployment
metadata:
  name: kiali
  namespace: ${WORKSPACE_NS}
spec:
  appRef:
    kind: ClusterApp
    name: ${kiali_app}
---
apiVersion: apps.kommander.d2iq.io/v1alpha3
kind: AppDeployment
metadata:
  name: jaeger
  namespace: ${WORKSPACE_NS}
spec:
  appRef:
    kind: ClusterApp
    name: ${jaeger_app}
EOF

  echo "Kommander apps requested via AppDeployment in namespace: ${WORKSPACE_NS}"
  echo "  istio-helm: ${istio_app}"
  echo "  kiali:     ${kiali_app}"
  echo "  jaeger:    ${jaeger_app}"

  echo "Waiting for Istio CRDs (VirtualService/DestinationRule) to exist..."
  if ! wait_for_crd "virtualservices.networking.istio.io" 900; then
    warn "Timed out waiting for Istio VirtualService CRD; demo mesh resources may not sync until Istio is ready"
  fi
  if ! wait_for_crd "destinationrules.networking.istio.io" 900; then
    warn "Timed out waiting for Istio DestinationRule CRD; demo mesh resources may not sync until Istio is ready"
  fi
}

autodetect_kubeconfig

echo "Target cluster:"
kc cluster-info >/dev/null
kc config current-context

enable_kommander_apps

echo
echo "Installing/ensuring ArgoCD..."
kc apply -k clusters/rx-demo/argocd/bootstrap >/dev/null
kc -n "$ARGO_NS" rollout status deploy/argocd-server --timeout=600s >/dev/null

echo "Waiting for ArgoCD Application CRD..."
if ! wait_for_crd "applications.argoproj.io" 300; then
  fail "applications.argoproj.io CRD not ready after 300s"
fi

echo
echo "Creating ArgoCD project/app..."
kc apply -f clusters/rx-demo/argocd/apps/appproject.yaml >/dev/null
kc apply -f clusters/rx-demo/argocd/apps/application.yaml >/dev/null

kc -n "$ARGO_NS" patch application "$APP_NAME" --type merge \
  -p "{\"spec\":{\"source\":{\"repoURL\":\"${REPO_URL}\",\"targetRevision\":\"${BRANCH}\"}}}" >/dev/null
kc -n "$ARGO_NS" annotate application "$APP_NAME" argocd.argoproj.io/refresh=hard --overwrite >/dev/null

echo
echo "ArgoCD:"
kc -n "$ARGO_NS" get application "$APP_NAME" -o wide || true

argo_lb_ip="$(kc -n "$ARGO_NS" get svc argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
argo_lb_host="$(kc -n "$ARGO_NS" get svc argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"

if [[ -n "${argo_lb_ip}" ]]; then
  echo "  UI: https://${argo_lb_ip}/ (user: admin)"
elif [[ -n "${argo_lb_host}" ]]; then
  echo "  UI: https://${argo_lb_host}/ (user: admin)"
else
  echo "  UI: (no LoadBalancer) use: kubectl -n ${ARGO_NS} port-forward svc/argocd-server 8443:443"
  echo "      then open: https://localhost:8443/ (user: admin)"
fi
echo "  Initial password:"
echo "    kubectl -n ${ARGO_NS} get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d && echo"

echo
echo "Demo app (Istio ingress):"
istio_ip="$(kc -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
if [[ -n "${istio_ip}" ]]; then
  echo "  URL: http://${istio_ip}/"
else
  echo "  Ingress service not ready or no LoadBalancer yet:"
  echo "    kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide"
fi

echo
echo "Demo Wall:"
demo_wall_ip="$(kc -n demo-ops get svc demo-wall -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
if [[ -n "${demo_wall_ip}" ]]; then
  echo "  URL: http://${demo_wall_ip}/"
else
  echo "  Service not ready yet (ArgoCD will create it during sync):"
  echo "    kubectl -n demo-ops get svc demo-wall -o wide"
fi
