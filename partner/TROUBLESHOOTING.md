# Troubleshooting

## No traffic visible
- Ensure branch is not `scenario/load-off`.
- Check `demo-loadgen` replicas in `demo-ops`.
- Switch to `scenario/load-peak` for stronger signal.

## Flux not applying changes
- Confirm `GitRepository` branch value is correct.
- Reconcile source first, then Kustomizations.
- Verify `platform/apps/mesh/ops-loadgen` are `Ready=True`.

## Kiali graph weak
- Increase load (`scenario/load-peak`).
- Wait one telemetry window and refresh.

## Traces missing in Jaeger
- Confirm OTLP endpoint in `apps/otel-shop-lite/base/configmap.yaml`.
- Verify requests are flowing through frontend.

## Logs not found in Loki
- Confirm logging pipeline is active.
- Filter by service label, then narrow by trace_id.