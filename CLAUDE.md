# CLAUDE.md — Nutanix-Demo

This is a **branch-driven GitOps demo** for NKP Rx. The control plane is ArgoCD switching `targetRevision`, not live YAML edits. Keep that mental model as your north star.

---

## Quick orientation

| Question | Go here |
|---|---|
| What is this repo? | `docs/architect.md` §1–2 |
| **How do I run the demo?** | **`docs/DEMO-GUIDE.md`** ← single source of truth for operators |
| Which features to show in NKP console? | `docs/NKP-CONSOLE-GUIDE.md` |
| Scenario branches and intent | `docs/DEMO-GUIDE.md §4` |
| Get On event (2-hr partner demo) | `docs/Get-On-Event-Track.md` |
| Troubleshooting / reset | `docs/TROUBLESHOOTING.md`, `docs/RESET.md` |
| Full technical spec | `docs/demo-spec.md` |
| Architecture deep-dive | `docs/architect.md` |
| **Current improvement backlog** | **`PROGRESS.md`** (repo root) |

---

## Multi-session work rule

**Always update `PROGRESS.md` (repo root) at the end of every work block.** This prevents context loss across compaction. Record:
- What was just implemented (with file paths)
- What is pending (from the backlog)
- Any decisions made or constraints discovered

Link new improvement ideas into `PROGRESS.md` immediately when they arise — don't leave them only in the conversation.

---

## Repo layout (at a glance)

```
clusters/rx-demo/argocd/    ArgoCD bootstrap + Application manifest
platform/                   Namespaces, RBAC, quotas, Gatekeeper policy
apps/otel-shop-lite/        App manifests, v1/v2 deployments, fault overlays
mesh/istio/                 Istio Gateway / VirtualService / DestinationRule overlays
ops/loadgen/                k6 load generator overlays (baseline / peak / off)
ops/demo-wall/              In-cluster KPI wall (auto-refresh every 5 s)
ops/demo-wall-local/        Standalone local KPI wall (operator laptop / PS1 launcher)
docs/                       All documentation — operator guides, architecture, spec
prereqs/                    Required / optional / sensitive-template grouping
scripts/                    bootstrap-demo.sh, print-access.sh, install-kubectl.sh
obsolete/                   Superseded documents kept for historical reference
auth/                       Kubeconfigs — intentionally git-ignored, never commit
```

---

## How the demo is controlled

ArgoCD Application `rx-demo` watches this repo and applies the Kustomize root at `clusters/rx-demo/argocd/root/kustomization.yaml`. Scenario state is set by changing `spec.source.targetRevision` to a `scenario/*` branch.

**Switch scenario (copy-paste):**
```bash
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

---

## Scenario branches

| Branch | App overlay | Canary | Load |
|---|---|---|---|
| `scenario/baseline` | normal | weight-0 (100% v1) | baseline |
| `scenario/load-off` | normal | weight-0 | **off** |
| `scenario/load-peak` | normal | weight-0 | peak |
| `scenario/canary-10` | normal | 90/10 | baseline |
| `scenario/canary-50` | normal | 50/50 | baseline |
| `scenario/canary-100` | normal | 0/100 | baseline |
| `scenario/incident-latency` | latency fault | 90/10 | baseline |
| `scenario/incident-error` | error fault (10%) | 90/10 | baseline |
| `scenario/mirror-v2` | normal | mirror (Beat 9) | baseline |
| `scenario/keda-checkout` | normal | weight-0 | KEDA-driven |
| `scenario/quota-pressure` | quota-pressure | weight-0 | baseline |
| `scenario/policy-enforce` | normal | weight-0 | baseline |
| `scenario/node-failure` | node-failure (2-replica HA + PDBs) | weight-0 | baseline |
| `scenario/node-autoscale` | node-pressure (6 × 2CPU pause pods) | weight-0 | baseline |

Always end sessions on `scenario/load-off`.

---

## Working rules (must follow)

- **Never merge `scenario/*` into `main`.** Scenario branches are runtime demo states, not feature branches.
- **No live YAML edits** in the cluster during a demo. Change the branch; let ArgoCD reconcile.
- **One GitOps controller per namespace.** ArgoCD owns `demo-app` and `demo-ops`; do not let other controllers (Flux, Helm operator) touch those namespaces.
- **Never commit secrets or kubeconfigs.** `auth/` is git-ignored. If you see credentials in a diff, stop and flag it immediately.
- **Keep core components consistent** across `main` and all `scenario/*` branches. Core components: `ops/demo-wall/`, `ops/demo-wall-local/`, `docs/`, `scripts/`, `platform/`. Diverge only when a scenario explicitly requires it, and document the reason in `docs/demo-spec.md`.

---

## Making changes

### Add a scenario
1. Branch off from the closest existing `scenario/*`.
2. Edit overlay selectors in:
   - `apps/otel-shop-lite/kustomization.yaml`
   - `mesh/istio/kustomization.yaml`
   - `ops/loadgen/kustomization.yaml`
3. Validate: `kubectl kustomize clusters/rx-demo/argocd/root`
4. Add an entry to the scenario table in `docs/DEMO-GUIDE.md §4` and update `SCENARIO_META` in `ops/demo-wall/server.py`.

### Change canary weights
Edit or add an overlay under `mesh/istio/overlays/`, then point `mesh/istio/kustomization.yaml` at it.

### Change load profile
Edit or add an overlay under `ops/loadgen/overlays/`, then point `ops/loadgen/kustomization.yaml` at it.

### Adjust policy
Edit `platform/policy/demo-guardrails.yaml`. Keep `enforcementAction: dryrun` unless you explicitly intend to block admission.

---

## Exploration guidance

- Read `docs/architect.md` first; it is structured so you can load only the section you need.
- For discovery, use `rg` (ripgrep) before opening files.
- For manifests, validate with `kubectl kustomize <path>` rather than reading raw YAML in isolation.
- Avoid reading large files in full — use line-range slices when a targeted section suffices.

---

## Key paths (quick reference)

| Purpose | Path |
|---|---|
| ArgoCD Application | `clusters/rx-demo/argocd/apps/application.yaml` |
| Kustomize root | `clusters/rx-demo/argocd/root/kustomization.yaml` |
| App overlay selector | `apps/otel-shop-lite/kustomization.yaml` |
| Mesh overlay selector | `mesh/istio/kustomization.yaml` |
| Load overlay selector | `ops/loadgen/kustomization.yaml` |
| Gatekeeper policy bundle | `platform/policy/demo-guardrails.yaml` |
| App source (Python) | `apps/otel-shop-lite/src/` |
| Bootstrap script | `scripts/bootstrap-demo.sh` |
| Access URL printer | `scripts/print-access.sh` |
| Operator guide | `docs/DEMO-GUIDE.md` |
| NKP console beats | `docs/NKP-CONSOLE-GUIDE.md` |

---

## Fault injection reference

`payment-mock-v2` is patched via env overlay:

| Overlay | `FAIL_MODE` | Effect |
|---|---|---|
| `normal` | `ok` | No fault |
| `incident-latency` | `latency` | `LATENCY_MS=1000` added to every response |
| `incident-error` | `error` | `ERROR_RATE=0.10` — 10% of calls return 5xx |

Traces go to Jaeger (OTLP), metrics to Prometheus, logs include `trace_id`/`span_id` for correlation.

---

## Demo Wall KPI contract

Refreshes every 5 s from `ops/demo-wall/`. Cards shown:

| Card | Source | Thresholds |
|---|---|---|
| CD Success Rate | ArgoCD Application status | good = Synced+Healthy |
| Canary Weight v2 | Istio VirtualService weights | informational |
| Policy Compliance | Gatekeeper constraint violations | good ≥ 95%, warn ≥ 60% |
| Rollback SLA Target | Static target | < 3 minutes |
