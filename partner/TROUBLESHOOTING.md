# Troubleshooting

## No traffic visible
- Ensure branch is not `scenario/load-off`.
- Check `demo-loadgen` replicas in `demo-ops`.
- Switch to `scenario/load-peak` for stronger signal.

## ArgoCD not applying changes
- Check Argo app status:
  - `kubectl -n argocd get application rx-demo -o wide`
- If `OutOfSync`, wait for auto-sync or force refresh:
  - `kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite`
- If `Missing/Degraded`, inspect:
  - `kubectl -n argocd describe application rx-demo`

## Kiali graph weak
- Increase load (`scenario/load-peak`).
- Wait one telemetry window and refresh.

## Traces missing in Jaeger
- Confirm OTLP endpoint in `apps/otel-shop-lite/base/configmap.yaml`.
- Verify requests are flowing through frontend.

## Logs not found in Loki
- Confirm logging pipeline is active.
- Filter by service label, then narrow by trace_id.

## Demo Wall not reachable
- Check service external IP:
  - `kubectl -n demo-ops get svc demo-wall -o wide`
- Check pod:
  - `kubectl -n demo-ops get pods -l app=demo-wall -o wide`
