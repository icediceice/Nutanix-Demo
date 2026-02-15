# Partner Quickstart (ArgoCD)

This demo is branch-driven. No live YAML edits are required during the session.

Use:
- Full step-by-step: `partner/RUNBOOK.md`
- Operator commands: `partner/COMMANDS.md`

## 0) Clone repo + kubeconfig
```bash
git clone https://github.com/icediceice/Nutanix-Demo.git
cd Nutanix-Demo
mkdir -p auth
```

Place your workload cluster kubeconfig at:
- `auth/workload02.conf`

Example usage:
```bash
kubectl --kubeconfig auth/workload02.conf get nodes
```

Note: `auth/` is intentionally ignored by git.

## 1) One-time setup
Run the bootstrap (fool-proof on a new workload cluster):
- `./scripts/bootstrap-demo.sh --branch scenario/load-off`

Optional (if you manage multiple kubeconfigs):
- `./scripts/bootstrap-demo.sh --kubeconfig auth/workload02.conf --branch scenario/load-off`

Verify:
- `kubectl -n argocd get application rx-demo -o wide`
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
