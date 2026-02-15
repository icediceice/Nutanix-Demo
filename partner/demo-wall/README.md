# Demo Wall

Audience-facing visual status board for CD + demo runtime state.

## What it shows
- Scenario branch and revision
- CD sync/health status
- loadgen desired/ready replicas
- canary weights (v1/v2)
- policy summary (pass/warn/fail/error)
- KPI cards

## Recommended (in-cluster)
The demo deploys an in-cluster Demo Wall service in `demo-ops`:
```bash
kubectl -n demo-ops get svc demo-wall -o wide
```
Open: `http://<DEMO_WALL_LB_IP>/`

Fallback:
```bash
kubectl -n demo-ops port-forward svc/demo-wall 9090:80
```
Open: `http://localhost:9090`

## Legacy (local script)
The local PowerShell script (`partner/demo-wall/start-demo-wall.ps1`) is not used in the ArgoCD demo.
