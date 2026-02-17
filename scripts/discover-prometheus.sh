#!/usr/bin/env bash
set -euo pipefail

# Best-effort Prometheus endpoint discovery for the KEDA demo.
# This is intentionally heuristic because Prometheus service names vary by platform (NKP, OpenShift, etc.).

KUBECTL="${KUBECTL:-kubectl}"

KUBECONFIG_PATH=""
CONTEXT_NAME=""
APPLY=0

TARGET_NAMESPACE="${TARGET_NAMESPACE:-demo-app}"
CONFIGMAP_NAME="${CONFIGMAP_NAME:-keda-prometheus}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/discover-prometheus.sh [--kubeconfig PATH] [--context NAME] [--apply]

What it does:
  - Discovers a likely in-cluster Prometheus HTTP endpoint (best-effort).
  - Prints the chosen serverAddress.
  - If --apply is set, applies demo-app/ConfigMap keda-prometheus with that serverAddress.

Override:
  - Set PROMETHEUS_SERVER_ADDRESS to force the value (example: http://prometheus.monitoring.svc:9090)
EOF
}

fail() { echo "FAIL: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) KUBECONFIG_PATH="${2:-}"; shift 2 ;;
    --context) CONTEXT_NAME="${2:-}"; shift 2 ;;
    --apply) APPLY=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown arg: $1 (use --help)" ;;
  esac
done

kc() {
  local args=()
  if [[ -n "${KUBECONFIG_PATH}" ]]; then args+=(--kubeconfig "${KUBECONFIG_PATH}"); fi
  if [[ -n "${CONTEXT_NAME}" ]]; then args+=(--context "${CONTEXT_NAME}"); fi
  "$KUBECTL" "${args[@]}" "$@"
}

svc_port_9090() {
  local ns="$1"
  local name="$2"
  # Print 9090 if that port exists, else empty.
  kc -n "$ns" get svc "$name" -o jsonpath='{range .spec.ports[*]}{.port}{"\n"}{end}' 2>/dev/null | awk '$1==9090{print $1; exit 0}'
}

discover_server() {
  if [[ -n "${PROMETHEUS_SERVER_ADDRESS:-}" ]]; then
    echo "${PROMETHEUS_SERVER_ADDRESS}"
    return 0
  fi

  # Known/common Prometheus service names and namespaces (prefer Kommander default workspace).
  local -a preferred=(
    "kommander-default-workspace kube-prometheus-stack-prometheus"
    "monitoring kube-prometheus-stack-prometheus"
    "monitoring prometheus-kube-prometheus-prometheus"
    "monitoring prometheus-operated"
    "prometheus prometheus"
  )
  local ns name
  for pair in "${preferred[@]}"; do
    ns="${pair%% *}"
    name="${pair##* }"
    if kc -n "$ns" get svc "$name" >/dev/null 2>&1; then
      if [[ -n "$(svc_port_9090 "$ns" "$name")" ]]; then
        echo "http://${name}.${ns}.svc.cluster.local:9090"
        return 0
      fi
    fi
  done

  # Heuristic scan: any Service with "prometheus" in its name that exposes port 9090.
  # jsonpath prints: namespace<TAB>name<TAB>ports...
  local line
  line="$(
    kc get svc -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{range .spec.ports[*]}{.port}{" "}{end}{"\n"}{end}' 2>/dev/null \
      | awk 'tolower($2) ~ /prometheus/ && $0 ~ /(^|[ \t])9090([ \t]|$)/ { print $1 "\t" $2; exit 0 }' || true
  )"
  if [[ -n "$line" ]]; then
    ns="$(echo "$line" | awk '{print $1}')"
    name="$(echo "$line" | awk '{print $2}')"
    echo "http://${name}.${ns}.svc.cluster.local:9090"
    return 0
  fi

  return 1
}

server="$(discover_server || true)"
if [[ -z "$server" ]]; then
  warn "Could not auto-discover a Prometheus service endpoint."
  warn "Set PROMETHEUS_SERVER_ADDRESS or update apps/otel-shop-lite/overlays/keda-checkout/keda-prometheus-configmap.yaml"
  exit 0
fi

echo "Prometheus serverAddress: ${server}"

if [[ "$APPLY" -eq 1 ]]; then
  # Ensure namespace exists so we can apply the ConfigMap even before ArgoCD sync creates demo-app.
  kc get ns "${TARGET_NAMESPACE}" >/dev/null 2>&1 || kc create ns "${TARGET_NAMESPACE}" >/dev/null 2>&1 || true

  cat <<EOF | kc apply -f - >/dev/null
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${CONFIGMAP_NAME}
  namespace: ${TARGET_NAMESPACE}
data:
  serverAddress: ${server}
EOF
  echo "Applied: ${TARGET_NAMESPACE}/ConfigMap ${CONFIGMAP_NAME}"
fi

