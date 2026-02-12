# Verification Checklist

## Day-before checks
1. Flux Kustomizations are `Ready=True`: `platform`, `apps`, `mesh`, `ops-loadgen`.
2. Kiali loads graph for `demo-app` with live edges.
3. Jaeger receives traces for `frontend`, `checkout-api`, `payment-mock`.
4. Grafana shows request/error/latency panels for demo services.
5. Loki query returns logs with `service` and `trace_id` fields.

## T-30 minutes checks
1. Set load profile to `baseline` and confirm request rate > 0.
2. Confirm current traffic overlay (start at `weight-0`).
3. Confirm incident overlay is `normal`.
4. Execute one canary step (`weight-10`) and verify Kiali edge shift.
5. Revert back to known-good commit and verify recovery.