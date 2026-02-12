# Reset

## Fast reset (recommended)
1. Set branch to `scenario/baseline`.
2. Reconcile Flux source and Kustomizations.
3. Verify Kiali/Grafana stabilize.

## Hard reset (last resort)
1. Delete namespaces `demo-app` and `demo-ops`.
2. Reconcile Flux.
3. Wait for full redeploy.

## Session end
Switch to `scenario/load-off` so loadgen is not left running.