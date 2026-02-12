# Demo Operator Runbook

## Baseline start
1. Confirm app overlay points to `apps/otel-shop-lite/overlays/normal`.
2. Confirm mesh overlay points to `mesh/istio/overlays/weight-0`.
3. Confirm load overlay points to `ops/loadgen/overlays/baseline`.
4. Commit and push. Wait for Flux reconcile.

## Canary sequence
1. Change mesh overlay to `weight-10`, commit/push, observe Kiali.
2. Change mesh overlay to `weight-50`, commit/push, observe dashboards.
3. Optionally move to `weight-100` if the story requires full cutover.

## Incident drill
1. Change app overlay to `incident-latency` or `incident-error`.
2. Commit/push and wait for rollout.
3. Show Kiali hotspot, pivot to Jaeger trace breakdown, then Loki logs.

## Recovery
1. Revert incident overlay to `normal`.
2. Revert traffic to `weight-0` or known-good weight.
3. Optionally set load overlay to `off` at session end.
4. If needed, recover by deleting `demo-app` and `demo-ops`; Flux will recreate.