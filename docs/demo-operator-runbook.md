# Demo Operator Runbook

## Baseline start
1. Confirm app overlay points to `apps/otel-shop-lite/overlays/normal`.
2. Confirm mesh overlay points to `mesh/istio/overlays/weight-0`.
3. Confirm load overlay points to `ops/loadgen/overlays/baseline`.
4. Switch ArgoCD `rx-demo` to `scenario/baseline` and wait for `Synced` + `Healthy`.

## Canary sequence
1. Switch to `scenario/canary-10`, observe Kiali.
2. Switch to `scenario/canary-50`, observe dashboards.
3. Optionally move to `weight-100` if the story requires full cutover.

## Incident drill
1. Switch to `scenario/incident-latency` or `scenario/incident-error`.
2. Wait for ArgoCD to sync and pods to roll.
3. Show Kiali hotspot, pivot to Jaeger trace breakdown, then Loki logs.

## Recovery
1. Switch back to `scenario/baseline` (or known-good scenario).
2. End on `scenario/load-off`.
3. If needed, recover by deleting `demo-app` and `demo-ops`; ArgoCD will recreate.
