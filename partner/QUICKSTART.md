# Partner Quickstart (ArgoCD)

This demo is branch-driven. No live YAML edits are required during the session.

Use:
- Full step-by-step: `partner/RUNBOOK.md`
- Operator commands: `partner/COMMANDS.md`

## 1) One-time setup
1. Install ArgoCD:
   - `kubectl apply -k clusters/rx-demo/argocd/bootstrap`
2. Create the demo app in ArgoCD:
   - `kubectl apply -f clusters/rx-demo/argocd/apps/appproject.yaml`
   - `kubectl apply -f clusters/rx-demo/argocd/apps/application.yaml`
3. Wait for `rx-demo` to be `Synced` and `Healthy`:
   - `kubectl -n argocd get application rx-demo -o wide`
4. Demo Wall (in-cluster):
   - `kubectl -n demo-ops get svc demo-wall -o wide`

## 2) Run baseline
Switch ArgoCD app to branch `scenario/baseline`.

Expected:
- app healthy
- canary at weight-0
- baseline load running

## 3) Switch scenarios
- Stop load: `scenario/load-off`
- Canary 10%: `scenario/canary-10`
- Canary 50%: `scenario/canary-50`
- Canary 100%: `scenario/canary-100`
- Incident latency: `scenario/incident-latency`
- Incident error: `scenario/incident-error`
- Peak load: `scenario/load-peak`
- Optional mirror: `scenario/mirror-v2`

## 4) End session safely
Switch to `scenario/load-off`.

## Legacy mode
Flux bootstrap still exists at `clusters/rx-demo/flux`, but ArgoCD is the recommended operator UI/status surface.
