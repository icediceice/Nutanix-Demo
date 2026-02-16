#!/usr/bin/env bash
set -euo pipefail

KUBECTL="${KUBECTL:-kubectl}"

# Always run from repo root so relative paths work no matter where the operator runs the script from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

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
                             [--mgmt-kubeconfig PATH] [--mgmt-context NAME]
                             [--workload-cluster-name NAME]
                             [--ghcr-username USER] [--ghcr-token-file PATH]
                             [--discover-prometheus]

What it does:
  1) (Optional) Enables required Kommander apps (Istio/Kiali/Jaeger) via AppDeployment (no UI clicks).
     If your workload cluster does not have Kommander CRDs locally, pass --mgmt-kubeconfig/--mgmt-context
     to point this step at the Kommander management cluster.
  2) Installs ArgoCD (LoadBalancer service) from clusters/rx-demo/argocd/bootstrap.
  3) Creates ArgoCD AppProject + Application and points it at a scenario branch.
  4) Prints the URLs/commands to access ArgoCD, the Demo App, and Demo Wall.
  5) (Optional) If --discover-prometheus is set and you are using a KEDA scenario branch, attempts to auto-set
     demo-app/ConfigMap keda-prometheus to a reachable Prometheus endpoint.
EOF
}

fail() { echo "FAIL: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

KUBECONFIG_PATH=""
CONTEXT_NAME=""
MGMT_KUBECONFIG_PATH=""
MGMT_CONTEXT_NAME=""
WORKLOAD_CLUSTER_NAME=""
REPO_URL="$REPO_URL_DEFAULT"
BRANCH="$BRANCH_DEFAULT"
SKIP_KOMMANDER_APPS=0
GHCR_USERNAME_ARG=""
GHCR_TOKEN_FILE=""
DISCOVER_PROMETHEUS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) KUBECONFIG_PATH="${2:-}"; shift 2 ;;
    --context) CONTEXT_NAME="${2:-}"; shift 2 ;;
    --mgmt-kubeconfig|--management-kubeconfig) MGMT_KUBECONFIG_PATH="${2:-}"; shift 2 ;;
    --mgmt-context|--management-context) MGMT_CONTEXT_NAME="${2:-}"; shift 2 ;;
    --workload-cluster-name) WORKLOAD_CLUSTER_NAME="${2:-}"; shift 2 ;;
    --repo) REPO_URL="${2:-}"; shift 2 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --workspace-namespace) WORKSPACE_NS="${2:-}"; shift 2 ;;
    --skip-kommander-apps) SKIP_KOMMANDER_APPS=1; shift 1 ;;
    --ghcr-username) GHCR_USERNAME_ARG="${2:-}"; shift 2 ;;
    --ghcr-token-file) GHCR_TOKEN_FILE="${2:-}"; shift 2 ;;
    --discover-prometheus) DISCOVER_PROMETHEUS=1; shift 1 ;;
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

kc_mgmt() {
  local args=()
  if [[ -n "${MGMT_KUBECONFIG_PATH}" ]]; then args+=(--kubeconfig "${MGMT_KUBECONFIG_PATH}"); fi
  if [[ -n "${MGMT_CONTEXT_NAME}" ]]; then args+=(--context "${MGMT_CONTEXT_NAME}"); fi
  "$KUBECTL" "${args[@]}" "$@"
}

ensure_ghcr_pull_secret() {
  # Demo app images may be private in GHCR; if so, workloads will stay in ImagePullBackOff until a pull secret exists.
  local ns="demo-app"
  local secret="ghcr-pull"
  local user="${GHCR_USERNAME_ARG:-${GHCR_USERNAME:-icediceice}}"
  local token="${GHCR_TOKEN:-}"

  if kc -n "${ns}" get secret "${secret}" >/dev/null 2>&1; then
    echo "${ns}/secret ${secret}: present"
    return 0
  fi

  # Make a best-effort to ensure the namespace exists so the secret can be applied early.
  if ! kc get ns "${ns}" >/dev/null 2>&1; then
    kc create ns "${ns}" >/dev/null 2>&1 || true
  fi

  # Prefer a token file if provided (safer than flags/env because it won't show up in shell history/process list).
  if [[ -z "${token}" && -n "${GHCR_TOKEN_FILE}" ]]; then
    if [[ -f "${GHCR_TOKEN_FILE}" ]]; then
      token="$(tr -d '\r\n' < "${GHCR_TOKEN_FILE}" | head -c 4096)"
    else
      warn "--ghcr-token-file provided but not found: ${GHCR_TOKEN_FILE}"
    fi
  fi

  # Optional convenience: if GitHub CLI is installed and the operator has already authenticated, reuse that token.
  if [[ -z "${token}" ]] && have gh; then
    token="$(gh auth token 2>/dev/null || true)"
  fi

  if [[ -z "${token}" ]]; then
    warn "${ns}/secret ${secret}: missing. Required if ghcr.io images are private."
    warn "Provide creds in one of these ways, then re-run:"
    warn "  1) Token file:"
    warn "     printf '%s' \"<GHCR_TOKEN>\" > auth/ghcr.token && chmod 600 auth/ghcr.token"
    warn "     ./scripts/bootstrap-demo.sh ... --ghcr-username ${user} --ghcr-token-file auth/ghcr.token"
    warn "  2) Env vars:"
    warn "     export GHCR_USERNAME=${user}"
    warn "     export GHCR_TOKEN='...'"
    warn "  3) GitHub CLI:"
    warn "     gh auth login"
    return 0
  fi

  kc -n "${ns}" create secret docker-registry "${secret}" \
    --docker-server=ghcr.io \
    --docker-username="${user}" \
    --docker-password="${token}" \
    --docker-email="unused@example.com" \
    --dry-run=client -o yaml | kc apply -f - >/dev/null

  echo "${ns}/secret ${secret}: applied"
}

maybe_set_keda_prometheus_endpoint() {
  # Best-effort only. Requires the discovery script and a KEDA scenario branch.
  if [[ "${DISCOVER_PROMETHEUS}" -ne 1 ]]; then
    return 0
  fi
  if [[ "${BRANCH}" != scenario/keda-* ]]; then
    return 0
  fi
  if [[ ! -f "${SCRIPT_DIR}/discover-prometheus.sh" ]]; then
    warn "discover-prometheus.sh not found; skipping Prometheus endpoint discovery"
    return 0
  fi

  local args=()
  if [[ -n "${KUBECONFIG_PATH}" ]]; then args+=(--kubeconfig "${KUBECONFIG_PATH}"); fi
  if [[ -n "${CONTEXT_NAME}" ]]; then args+=(--context "${CONTEXT_NAME}"); fi

  echo
  echo "Discovering Prometheus endpoint for KEDA..."
  "${SCRIPT_DIR}/discover-prometheus.sh" "${args[@]}" --apply || true
}

kommander_kc() {
  # If mgmt kubeconfig/context provided, use that for Kommander CRDs; else fall back to workload kubeconfig.
  if [[ -n "${MGMT_KUBECONFIG_PATH}" || -n "${MGMT_CONTEXT_NAME}" ]]; then
    kc_mgmt "$@"
  else
    kc "$@"
  fi
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
  candidates="$(kommander_kc get clusterapp -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -E "^${prefix}-" || true)"
  if [[ -z "$candidates" ]]; then
    return 1
  fi
  # Strip prefix and '-' to sort versions, then re-attach the name.
  # shellcheck disable=SC2016
  echo "$candidates" | awk -v p="${prefix}-" '{v=$0; sub(p,"",v); print v "\t" $0}' | sort -V | tail -n 1 | awk '{print $2}'
}

infer_workload_cluster_name() {
  if [[ -n "${WORKLOAD_CLUSTER_NAME}" ]]; then
    return 0
  fi

  # Best signal when available.
  local from_label
  from_label="$(kc get ns kube-system -o jsonpath='{.metadata.labels.kommander\.d2iq\.io/cluster-name}' 2>/dev/null || true)"
  if [[ -n "${from_label}" ]]; then
    WORKLOAD_CLUSTER_NAME="${from_label}"
    return 0
  fi

  # Common kubeconfig context format: user@cluster-name
  local ctx
  ctx="$(kc config current-context 2>/dev/null || true)"
  if [[ -n "${ctx}" ]]; then
    if [[ "${ctx}" == *@* ]]; then
      WORKLOAD_CLUSTER_NAME="${ctx##*@}"
    else
      WORKLOAD_CLUSTER_NAME="${ctx}"
    fi
  fi

  if [[ -z "${WORKLOAD_CLUSTER_NAME}" ]]; then
    fail "Could not infer workload cluster name from kubeconfig. Re-run with --workload-cluster-name <name>."
  fi
}

validate_workload_cluster_name() {
  # Ensure the selector will match a joined cluster in this workspace.
  if kommander_kc -n "${WORKSPACE_NS}" get kommandercluster "${WORKLOAD_CLUSTER_NAME}" >/dev/null 2>&1; then
    return 0
  fi

  local known
  known="$(kommander_kc -n "${WORKSPACE_NS}" get kommandercluster -o jsonpath='{range .items[*]}{.metadata.name}{" "}{end}' 2>/dev/null || true)"
  fail "KommanderCluster '${WORKLOAD_CLUSTER_NAME}' was not found in workspace namespace '${WORKSPACE_NS}'. Known clusters: ${known:-none}. Re-run with --workload-cluster-name <name> and correct --workspace-namespace."
}

enable_kommander_apps() {
  if [[ "$SKIP_KOMMANDER_APPS" -eq 1 ]]; then
    warn "Skipping Kommander app enablement (--skip-kommander-apps)"
    return 0
  fi

  # Kommander UI typically runs on the management cluster. Many workload clusters will not have
  # Kommander CRDs like AppDeployment/ClusterApp installed locally, even if they are attached.
  local out
  if ! out="$(kommander_kc get crd appdeployments.apps.kommander.d2iq.io -o name 2>&1)"; then
    if echo "$out" | grep -qi "forbidden"; then
      warn "RBAC blocked reading Kommander AppDeployment CRD (Forbidden); skipping Kommander app enablement."
      warn "If you want this automated, run with cluster-admin or enable apps via the Kommander management cluster."
      return 0
    fi
    warn "Kommander AppDeployment CRD not found on the current kubeconfig; skipping Kommander app enablement."
    warn "If your workload cluster is attached to Kommander, pass --mgmt-kubeconfig (management cluster) so this script can enable Istio/Kiali/Jaeger without UI clicks."
    return 0
  fi

  if ! out="$(kommander_kc get crd clusterapps.apps.kommander.d2iq.io -o name 2>&1)"; then
    if echo "$out" | grep -qi "forbidden"; then
      warn "RBAC blocked reading Kommander ClusterApp CRD (Forbidden); skipping Kommander app enablement."
      return 0
    fi
    warn "Kommander ClusterApp CRD not found on this cluster; skipping Kommander app enablement"
    return 0
  fi

  if [[ -n "${MGMT_KUBECONFIG_PATH}" || -n "${MGMT_CONTEXT_NAME}" ]]; then
    echo "Kommander enablement target: management kubeconfig/context"
  else
    echo "Kommander enablement target: workload kubeconfig/context"
  fi

  kommander_kc get ns "$WORKSPACE_NS" >/dev/null 2>&1 || kommander_kc create ns "$WORKSPACE_NS" >/dev/null

  local istio_app kiali_app jaeger_app
  istio_app="$(resolve_clusterapp "istio-helm" || true)"
  kiali_app="$(resolve_clusterapp "kiali" || true)"
  jaeger_app="$(resolve_clusterapp "jaeger" || true)"

  if [[ -z "$istio_app" || -z "$kiali_app" || -z "$jaeger_app" ]]; then
    warn "Could not resolve required ClusterApps (istio-helm/kiali/jaeger)."
    warn "Check: kubectl get clusterapp | grep -E '^(istio-helm|kiali|jaeger)-'"
    return 0
  fi

  infer_workload_cluster_name
  validate_workload_cluster_name

  local istio_ver kiali_ver jaeger_ver
  istio_ver="${istio_app#istio-helm-}"
  kiali_ver="${kiali_app#kiali-}"
  jaeger_ver="${jaeger_app#jaeger-}"

  cat <<EOF | kommander_kc apply -f - >/dev/null
apiVersion: apps.kommander.d2iq.io/v1alpha3
kind: AppDeployment
metadata:
  name: istio-helm
  namespace: ${WORKSPACE_NS}
spec:
  appRef:
    kind: ClusterApp
    name: ${istio_app}
  clusterSelector:
    matchExpressions:
      - key: kommander.d2iq.io/cluster-name
        operator: In
        values:
          - ${WORKLOAD_CLUSTER_NAME}
  clusterConfigOverrides:
    - appVersion: ${istio_ver}
      clusterSelector:
        matchExpressions:
          - key: kommander.d2iq.io/cluster-name
            operator: In
            values:
              - ${WORKLOAD_CLUSTER_NAME}
      configMapName: ""
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
  clusterSelector:
    matchExpressions:
      - key: kommander.d2iq.io/cluster-name
        operator: In
        values:
          - ${WORKLOAD_CLUSTER_NAME}
  clusterConfigOverrides:
    - appVersion: ${kiali_ver}
      clusterSelector:
        matchExpressions:
          - key: kommander.d2iq.io/cluster-name
            operator: In
            values:
              - ${WORKLOAD_CLUSTER_NAME}
      configMapName: ""
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
  clusterSelector:
    matchExpressions:
      - key: kommander.d2iq.io/cluster-name
        operator: In
        values:
          - ${WORKLOAD_CLUSTER_NAME}
  clusterConfigOverrides:
    - appVersion: ${jaeger_ver}
      clusterSelector:
        matchExpressions:
          - key: kommander.d2iq.io/cluster-name
            operator: In
            values:
              - ${WORKLOAD_CLUSTER_NAME}
      configMapName: ""
EOF

  echo "Kommander apps requested via AppDeployment in namespace: ${WORKSPACE_NS}"
  echo "  selector:  ${WORKLOAD_CLUSTER_NAME}"
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

maybe_suspend_demo_flux() {
  # If Flux demo objects exist (from older demo versions), they will fight with ArgoCD over the same resources.
  # We do not uninstall Flux; we only suspend the demo-specific Kustomizations if they exist.
  if ! kc get crd kustomizations.kustomize.toolkit.fluxcd.io >/dev/null 2>&1; then
    return 0
  fi

  local ns="flux-system"
  if ! kc get ns "${ns}" >/dev/null 2>&1; then
    return 0
  fi

  local -a ks=(platform apps mesh ops-loadgen)
  local found=0

  for k in "${ks[@]}"; do
    if kc -n "${ns}" get kustomization "${k}" >/dev/null 2>&1; then
      found=1
      local suspended
      suspended="$(kc -n "${ns}" get kustomization "${k}" -o jsonpath='{.spec.suspend}' 2>/dev/null || true)"
      if [[ "${suspended}" != "true" ]]; then
        warn "Detected Flux Kustomization ${ns}/${k} (not suspended). Suspending to avoid conflicts with ArgoCD demo."
        kc -n "${ns}" patch kustomization "${k}" --type merge -p '{"spec":{"suspend":true}}' >/dev/null || true
      else
        warn "Detected Flux Kustomization ${ns}/${k} (already suspended)."
      fi
    fi
  done

  if [[ "${found}" -eq 1 ]]; then
    warn "Flux demo objects were found under ${ns}. This demo runs via ArgoCD; keep these suspended (or delete them) to avoid drift/OutOfSync."
  fi
}

autodetect_kubeconfig

echo "Target cluster:"
kc cluster-info >/dev/null
kc config current-context

maybe_suspend_demo_flux

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
echo "Ensuring GHCR pull secret (optional)..."
ensure_ghcr_pull_secret

maybe_set_keda_prometheus_endpoint

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
