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
- If sync fails with `one or more synchronization tasks are not valid` and mentions missing CRDs, wait 30-60s and refresh.
  - Some CRDs are created asynchronously (example: Gatekeeper ConstraintTemplates create constraint CRDs).
  - This repo sets Argo sync option `SkipDryRunOnMissingResource=true` to avoid blocking first sync.

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

## Demo app not reachable externally
This repo routes `http://<ISTIO_INGRESS_LB_IP>/` through an Istio `Gateway` + `VirtualService`:
- Gateway: `istio-helm-gateway-ns/gateway demo-gateway`
- VirtualService: `demo-app/virtualservice frontend-ingress`

Checks:
- `kubectl -n istio-helm-gateway-ns get gateway demo-gateway -o yaml`
- `kubectl -n demo-app get virtualservice frontend-ingress -o yaml`
- `kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide`

If `demo-gateway` never serves traffic, the selector in `mesh/istio/gateway/demo-gateway.yaml` may not match your ingressgateway pods.
