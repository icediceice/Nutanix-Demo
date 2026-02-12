# Partner Quickstart

This demo is branch-driven. No YAML edits are required during the session.
Use `partner/COMMANDS.md` for copy/paste commands.
For audience visualization, run `partner/demo-wall/start-demo-wall.ps1`.
KPI/policy defaults are defined in `WOW.md`.

## 1) One-time setup
1. Update `clusters/rx-demo/flux/gitrepository.yaml` with your repo URL/branch.
2. Apply/sync `clusters/rx-demo/flux` in your NKP cluster.
3. Wait for Flux Kustomizations to be Ready:
   - `platform`
   - `apps`
   - `mesh`
   - `ops-loadgen`
4. Confirm Gatekeeper auto-installed:
   - `kubectl -n flux-system get helmrelease gatekeeper`
   - `kubectl get constrainttemplates.templates.gatekeeper.sh`

## 2) Run baseline
Switch Flux source to branch `scenario/baseline`.

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
