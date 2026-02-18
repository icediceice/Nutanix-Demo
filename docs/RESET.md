# Reset

## Fast reset (recommended)
1. Set branch to `scenario/baseline` (ArgoCD `targetRevision`).
2. Wait for ArgoCD `rx-demo` to be `Synced` and `Healthy`.
3. Verify Kiali/Grafana stabilize.

## Hard reset (last resort)
1. Delete namespaces `demo-app` and `demo-ops`.
2. ArgoCD will recreate on next sync.
3. Wait for full redeploy.

## Session end
Switch to `scenario/load-off` so loadgen is not left running.
