# KEDA Autoscaling (Prometheus) Demo

This repo includes an optional scenario branch that installs KEDA and demonstrates **scale-to-zero** autoscaling for `demo-app/Deployment checkout-api-v1` using a **Prometheus** trigger.

## Scenario
- Branch: `scenario/keda-checkout`
- What it does:
  - Installs KEDA (`platform/keda`)
  - Switches the app overlay to `apps/otel-shop-lite/overlays/keda-checkout`
  - Forces `checkout-api-v1` (and `checkout-api-v2`) to start at `replicas: 0`
  - Creates a `ScaledObject` that scales `checkout-api-v1` from 0..10 based on an Istio request-rate PromQL query

## Configure Prometheus Endpoint
KEDA needs a reachable Prometheus HTTP endpoint.

Default is set in:
- `demo-app/ConfigMap keda-prometheus` (`data.serverAddress`)

If your Prometheus service name differs, change `serverAddress` in:
- `apps/otel-shop-lite/overlays/keda-checkout/keda-prometheus-configmap.yaml`

### Automatic Discovery (Optional)
You can try best-effort endpoint discovery and apply it to the cluster:
```bash
./scripts/discover-prometheus.sh --apply
```

If you bootstrap directly into the KEDA scenario, you can also add:
```bash
./scripts/bootstrap-demo.sh ... --branch scenario/keda-checkout --discover-prometheus
```

## Validate In Cluster
1. Switch ArgoCD `rx-demo` to `scenario/keda-checkout` and wait for sync.
2. Confirm KEDA is running:
   - `kubectl -n keda get pods`
3. Confirm the ScaledObject exists:
   - `kubectl -n demo-app get scaledobject`
4. Confirm checkout starts at zero:
   - `kubectl -n demo-app get deploy checkout-api-v1 -o jsonpath='{.spec.replicas}{"\n"}'`
5. Under baseline load, within 1-2 minutes confirm scale up:
   - `kubectl -n demo-app get deploy checkout-api-v1 -w`
6. After traffic drops, confirm it scales back down to 0 after the cooldown window.

## If It Doesn't Scale
- Verify the Prometheus endpoint is reachable from inside the cluster.
- Verify the PromQL query returns non-zero values during checkout activity.
- If your Istio metrics labels differ, update the query in:
  - `apps/otel-shop-lite/overlays/keda-checkout/checkout-api-v1-scaledobject.yaml`

## OpenShift Notes (High Level)
KEDA is the same concept on OpenShift: install KEDA (usually via **OperatorHub**) and apply the same `ScaledObject`.

Key differences you may need to account for:
- Installation:
  - OpenShift commonly installs KEDA via OperatorHub (OLM) rather than applying the upstream YAML directly.
  - If you're using OpenShift GitOps (ArgoCD), you can still manage `ScaledObject` resources GitOps-style once the operator/CRDs exist.
- Prometheus connectivity:
  - OpenShift Monitoring (Prometheus/Thanos) is often secured (TLS/auth). KEDA may need auth headers, CA bundles, or a different endpoint.
  - Many teams point KEDA at a user-workload Prometheus or an in-cluster Prometheus they own for simpler demos.

