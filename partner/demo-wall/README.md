# Demo Wall

Read-only audience-facing visual status board for Flux + demo runtime state.

## What it shows
- Current Flux scenario branch (`GitRepository` spec ref)
- Flux artifact revision
- GitRepository Ready status
- Kustomization readiness table
- loadgen desired/ready replicas
- canary weights (v1/v2)
- policy summary (pass/warn/fail/error)
- KPI cards:
  - Flux Success Rate
  - Canary Weight v2
  - Policy Compliance
  - Rollback SLA Target

## Start it
```powershell
powershell -ExecutionPolicy Bypass -File .\partner\demo-wall\start-demo-wall.ps1
```

Open: `http://localhost:9090`

## Optional: run on another port
```powershell
powershell -ExecutionPolicy Bypass -File .\partner\demo-wall\start-demo-wall.ps1 -Port 9191
```

## Optional local UI links
The page includes quick links assuming these local forwards:

```powershell
kubectl -n istio-system port-forward svc/kiali 20001:20001
kubectl -n kommander port-forward svc/jaeger-query 16686:16686
kubectl -n kommander port-forward svc/kube-prometheus-stack-grafana 3000:80
```

## Notes
- Uses `kubectl get ... -o json` only (no writes).
- Stop server with `Ctrl+C`.
- If Kyverno policy report CRDs are not present, policy KPI falls back to zero values.
