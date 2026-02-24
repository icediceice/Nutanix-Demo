# Demo Improvement Progress

This file is the cross-session source of truth for what has been built, what is
pending, and decisions made. Update it at the end of every work block.

---

## Status key

| Symbol | Meaning |
|---|---|
| ✅ | Done |
| 🔄 | In progress this session |
| ⏳ | Planned — not started |
| ⏭️ | Skipped (reason noted) |

---

## Session log

### Session 11

**Implemented:**
- ✅ `scenario/node-autoscale` branch — demonstrates CAPI/Cluster Autoscaler provisioning new worker nodes
  - `platform/node-pressure/` — `demo-pressure` namespace (Istio disabled) + 6-replica Deployment using `pause:3.9` with `requests: cpu=2, memory=4Gi` per pod
  - `platform/kustomization.yaml` — adds `node-pressure` to resources on this branch only
  - `ops/demo-wall/server.py` — `get_autoscale_status()` returns worker node count (control-plane excluded) + pressure pod pending/running counts; added to `build_payload()` as `autoscale` key; SCENARIO_META entry added
  - `ops/demo-wall/index.html` — `nodeAutoscaleCard` (hidden except on node-autoscale) with pending count, worker node bar, and full sub-line
  - `docs/DEMO-GUIDE.md` — Beat 18b with pre-step (MachineDeployment annotation), watch commands, talking points, scale-down note; §3.5 times updated; §4 table row added
  - `CLAUDE.md` — scenario table row added

- ✅ KEDA scenario fully stabilised (keda-checkout branch fixes from same session):
  - PostSync `discover-prometheus` Job auto-detects Prometheus endpoint and patches ConfigMap + ScaledObject; `sidecar.istio.io/inject: "false"` prevents Istio blocking job completion
  - `application.yaml`: `RespectIgnoreDifferences=true`, `ignoreDifferences` for ConfigMap/ScaledObject serverAddress and Deployment spec.replicas
  - Quota: `limits.cpu: 40`, `limits.memory: 28Gi` (Istio sidecar adds ~2000m CPU + 1024Mi per pod)

**Pre-requisite for node-autoscale (documented in Beat 18b):**
NKP uses ClusterClass topology — the autoscaler max annotation must be patched on the **Cluster** object, not the MachineDeployment (the topology controller reverts direct MD patches immediately):
```
kubectl --kubeconfig auth/C01/nkp.conf -n kommander-default-workspace \
  patch cluster workload02 --type json \
  -p '[{"op":"replace","path":"/spec/topology/workers/machineDeployments/0/metadata/annotations/cluster.x-k8s.io~1cluster-api-autoscaler-node-group-max-size","value":"8"}]'
```
Also: `progressDeadlineSeconds: 1800` added to pressure Deployment so ArgoCD doesn't mark it Degraded while nodes are provisioning (~3-5 min).

---

### Session 10

**Implemented:**
- ✅ Restructured `docs/DEMO-GUIDE.md` §3 from 17 flat beats into a **4-Act narrative** with audience tags, time estimates, and transition scripts
  - **Act 1 — "The Platform"** (~10 min): Beats 1–4. Merged old Beats 3+4 (add-ons + quotas) and old Beats 5+9 (RBAC + policy dryrun) into tighter "guardrails" beats.
  - **Act 2 — "Ship It"** (~18 min): Beats 5–9. Added Beat 7 (distributed traces in Jaeger — existing trace link feature, no code needed) and Beat 9 (shadow testing with `scenario/mirror-v2` — existing scenario, no code needed).
  - **Act 3 — "Break It, Find It, Fix It"** (~18 min): Beats 10–14. Added Beat 12 (error injection with `scenario/incident-error` — existing scenario) and Beat 13 (trace → log correlation via `kubectl logs` grep or Loki query).
  - **Act 4 — "Go Deeper"**: Beats 15–18. Organized as two self-contained tracks: Track A (Guardrails & Compliance: quota + policy enforce) and Track B (Resilience & Autoscaling: node failure + KEDA). Beat 16 callbacks to Act 1 dryrun for narrative arc.
  - Beat 19: End session (`scenario/load-off`)
- ✅ Added **§3.5 Recommended run paths** — 5 audience profiles (exec, dev, ops, infra, full) with beat lists and time estimates
- ✅ Updated **§4 scenario reference table** — added "Used in" column mapping each branch to its beat numbers; updated `mirror-v2` logical next to `canary-10`
- ✅ Updated `CLAUDE.md` scenario table: `mirror-v2` now notes its demo beat (Beat 9)

**Files changed:**
- `docs/DEMO-GUIDE.md` — major rewrite of §3, new §3.5, updated §4
- `docs/Get-On-Event-Track.md` — **new file**: 2-hour presentation plan for Get On distributor partner event. Includes 11-segment timeline, partner-focused talking points per beat, pre-event checklist, competitive positioning notes, partner opportunity framing, post-event follow-up, and quick reference card template.
- `CLAUDE.md` — scenario table annotation for mirror-v2; added Get On event track to quick orientation table
- `PROGRESS.md` — this entry

**No code changes.** No new scenarios, overlays, or server.py modifications. Pure documentation.

---

### Session 9

**Implemented:**
- ✅ Documented `scenario/node-failure` — was fully implemented (overlay, SCENARIO_META, RBAC) but had no DEMO-GUIDE beat or CLAUDE.md entry
  - Added Beat 17 to `docs/DEMO-GUIDE.md` — cordon/drain walkthrough, NKP CAPI auto-replace narrative, PDB explanation
  - Added row to DEMO-GUIDE.md §4 scenario reference table
- ✅ Added 3 missing branches to `CLAUDE.md` scenario table: `quota-pressure`, `policy-enforce`, `node-failure`
- ✅ Fixed Beat 15 error message: example pod has `app` label but is missing `version` — Gatekeeper rejects with "label 'version' is required", not "label 'app' is required"

**Branch staleness audit (all 3 undocumented branches):**
All three branches (`node-failure`, `policy-enforce`, `quota-pressure`) are stale — forked before Sessions 6-8 and missing: OTEL exporter fix, clipboard copy fix, trace ID display changes, `seed_demo_wall_access()` in bootstrap, CLAUDE.md. They also carry artifacts (AGENTS.md, duplicate README KEDA section, unnecessary `- keda` in platform/kustomization.yaml). They need a rebase onto current main before use.

---

### Session 8

**Implemented:**
- ✅ Fixed Jaeger tracing — traces now appear in Jaeger with all 4 app services
  - Root cause: `otel-shop-config` ConfigMap pointed at `jaeger-collector.kommander.svc.cluster.local:4317` — both the service name and namespace were wrong (namespace `kommander` doesn't exist)
  - Fix: updated to `jaeger-jaeger-operator-jaeger-collector.istio-system.svc.cluster.local:4317` (the actual Jaeger Operator-deployed collector)
  - Applied to `main` + all 13 `scenario/*` branches
  - Verified: Jaeger API now returns services `frontend`, `catalog-api`, `checkout-api`, `payment-mock`; traces with 7 spans confirmed
- Note: Jaeger UI is served at base path `/dkp/jaeger/` (NKP convention); API path is `/dkp/jaeger/api/...`

**Commits:**
- `faf32fa` on `main` — fix: point OTEL exporter at actual Jaeger collector in istio-system
- Cherry-picked to all 13 scenario branches

---

### Session 3

**Implemented:**
- ✅ Trace ID → Jaeger deep link in storefront (`apps/otel-shop-lite/src/services/frontend.py`)
  - `/checkout` endpoint now returns `trace_id` (32-char hex OTel trace ID)
  - Template reads `JAEGER_QUERY_URL` env var (default: empty = copy-to-clipboard mode)
  - Bag panel shows a "Last Trace" badge after every checkout; links directly to Jaeger if URL is configured
- ✅ Scenario intent + "Next →" cue in Demo Wall (`ops/demo-wall/server.py` + `ops/demo-wall/index.html`)
  - `SCENARIO_META` dict maps every branch to a 1-line intent string and the logical next branch
  - Scenario card in Demo Wall shows the intent sub-line and a "Next →" hint
- ✅ Consolidated operator guide (`docs/DEMO-GUIDE.md`) — replaces RUNBOOK.md + QUICKSTART.md + COMMANDS.md
- ✅ NKP console platform guide (`docs/NKP-CONSOLE-GUIDE.md`) — maps each platform beat to the right NKP UI surface
- ✅ CLAUDE.md progress-doc rule added — ensures future sessions update this file
- ✅ Obsolete docs moved to `obsolete/` — RUNBOOK, QUICKSTART, COMMANDS, SCENARIOS, showtimes, kpi/README, WOW, AGENTS, argocd-quickstart, demo-operator-runbook
- ✅ `partner/` directory dissolved — all docs moved to `docs/`, demo-wall assets moved to `ops/demo-wall-local/`
- ✅ All cross-references updated across CLAUDE.md, README.md, docs/architect.md, docs/demo-spec.md

**Skipped:**
- ⏭️ `scripts/switch-scenario.sh` — ArgoCD UI branch switch is already simple enough; user confirmed skip

**Commits on main (pending push to scenario branches):**
- `57efcd4` — refactor: consolidate docs, add trace link, scenario intent, progress tracker
- `4c233be` — docs: retire obsolete docs/ files and fix stale references
- `0da585c` — refactor: dissolve partner/ into docs/ and ops/

---

### Session 2

**Implemented:**
- ✅ Nutanix brand color scheme across all three UIs (storefront v1+v2, ops demo-wall, partner demo-wall)
  - Colors: Blue `#0091DA`, Atlantis Green `#AFD135`, Dark Navy `#003B5C`
  - Both storefront themes are dark (v1 = blue-accent, v2 = green-accent)
- ✅ Storefront full redesign — editorial hero, product cards with SVG art, "Your Bag" sidebar, sticky header
  - Fonts: Rubik (display) + DM Sans (body)
- ✅ ops/demo-wall/index.html — redesigned with Nutanix palette, brand mark, section labels, footer
- ✅ partner/demo-wall/index.html — same treatment, pill-link quick links

---

### Session 1

**Implemented:**
- ✅ `CLAUDE.md` created (Claude-native init file)
- ✅ `partner/NKP-CONSOLE-GUIDE.md` created
- ✅ `memory/MEMORY.md` created

---

### Session 7

**Implemented:**
- ✅ Trace ID — remove copy button entirely; show full 32-char ID as selectable text
  - `apps/otel-shop-lite/src/services/frontend.py`: removed `copyTrace()`, removed 16-char truncation in `showTrace()`; without Jaeger URL the trace ID renders as `<code class="trace-id">` with `user-select:all` so a single click selects all for Ctrl+C; with Jaeger URL the link shows the full ID.
  - CSS `.trace-copy` replaced by `.trace-id` (monospace, `word-break:break-all`, `user-select:all`, `cursor:text`).
- ✅ quickref.html copy buttons — fixed root cause of silent failures
  - Root cause: `copyText()` tried `navigator.clipboard.writeText()` first on HTTPS; when permission denied the `.catch()` fallback called `execCommand("copy")` **asynchronously** (user gesture expired → always fails silently).
  - Fix: always try `execCommand("copy")` synchronously first (still inside click handler, user gesture live); only fall back to async Clipboard API if `execCommand` returns false.
  - Added `user-select:all` to `.cred-val` and `.cmd-box` — text is always selectable even if button fails.

**Commits on main:**
- `977ede0` — fix: clipboard copy works on HTTP (execCommand sync fallback) [Session 6]

---

### Session 6

**Implemented:**
- ✅ Clipboard copy works on HTTP (no HTTPS required)
  - `ops/demo-wall/quickref.html`: rewrote `copyText()` with `isSecureContext`-first pattern — on HTTP calls `execFallback()` synchronously (still inside click handler, user gesture live), on HTTPS uses async Clipboard API with sync fallback. No false "Copied!" on failure.
  - `apps/otel-shop-lite/src/services/frontend.py`: added `copyTrace(el)` helper with same pattern; replaced bare `navigator.clipboard.writeText()` inline onclick with `copyTrace(this)`.
  - JS validated with `node --check` on rendered template.
  - Cherry-picked to all 13 scenario branches (conflict-resolved on `policy-enforce` and `quota-pressure` — both had an older inline onclick with `writeText(\'' + id + '\')`).

**Commits on main:**
- `977ede0` — fix: clipboard copy works on HTTP (execCommand sync fallback)

---

### Session 5

**Implemented:**
- ✅ `scenario/node-failure` — worker node resilience demo
  - `ops/demo-wall/rbac.yaml`: `nodes` + `pods` get/list/watch added to `demo-wall-read` ClusterRole
  - `ops/demo-wall/server.py`: `get_node_status()` returns ready/total + per-node status; `get_pod_placement()` returns pod-to-node mapping grouped by `{app}-{version}`; both exposed as `nodes`/`pods` in `/api/status`; `scenario/node-failure` added to `SCENARIO_META`
  - `ops/demo-wall/index.html`: Node Health card (always visible, shows `X / N Ready`, NotReady node names); pod placement sub-rows under each workload row (name, node, phase, color-coded)
  - `apps/otel-shop-lite/overlays/node-failure/`: 2 replicas + `preferredDuringScheduling` anti-affinity (spread across nodes) for all 4 v1 services; PodDisruptionBudgets (`minAvailable: 1`)
  - `scenario/node-failure` branch: forked from `scenario/baseline`, uses `overlays/node-failure`, `weight-0` mesh, `baseline` load
  - Cherry-picked to all 13 scenario branches (conflict-resolved `policy-enforce` + `quota-pressure` via `git checkout main -- <files>`)

**Commits on main:**
- `6bbada7` — feat: scenario/node-failure — worker node resilience demo

**Commits on scenario/node-failure:**
- cherry-pick of `6bbada7` + `50b38a1` (overlay selector)

---

### Session 4

**Implemented:**
- ✅ Operator Quick Reference page (`ops/demo-wall/quickref.html`) at `/quickref`
  - Pre-demo checklist
  - Platform Access table with username/password shown prominently + one-click copy buttons
  - Port-forward commands section (auto-hides when all tools have LoadBalancer URLs)
  - Scenario reference table (live from `/api/status` payload)
  - Environment Setup guide — which env vars to set and the exact `kubectl` commands to get each credential
  - Switch-scenario kubectl command with copy button
- ✅ `server.py`: `/quickref` route + `scenarios[]` added to `/api/status` JSON payload
- ✅ `index.html`: "Quick Ref ↗" button in header linking to `/quickref`
- ✅ `kustomization.yaml`: `quickref.html` added to ConfigMap generator

**Commits:**
- `461b246` — feat: add operator Quick Reference page with credentials

---

## Improvement backlog

Priority: **High** = do next session | **Med** = plan soon | **Low** = nice to have

| # | Suggestion | Priority | Status | Notes |
|---|---|---|---|---|
| 1 | Trace ID → Jaeger deep link in storefront | High | ✅ Done | `JAEGER_QUERY_URL` env var controls the link target |
| 2 | `scripts/switch-scenario.sh` wrapper | Low | ⏭️ Skipped | ArgoCD UI is sufficient per user |
| 3 | Scenario intent + next-up cue in Demo Wall | High | ✅ Done | `SCENARIO_META` dict in server.py |
| 4 | Quota utilization card in Demo Wall | Med | ✅ Done | `get_quota_status()` in server.py; progress bar green/warn/red; always visible when quota exists |
| 5 | `scenario/quota-pressure` branch | Med | ✅ Done | 20× pause-container Deployment fills ~75% pod quota; Demo Wall bar goes amber |
| 6 | `scenario/policy-enforce` branch | Med | ✅ Done | `platform/policy/overlays/enforce/` patches K8sDemoRequiredLabels to deny; pod rejected at admission |
| 7 | Per-constraint breakdown in Demo Wall policy card | Med | ⏳ Planned | Show each constraint name + violation count instead of aggregate |
| 8 | Consolidated operator docs | High | ✅ Done | `partner/DEMO-GUIDE.md` |
| 9 | Favicon (Nutanix X mark, 32×32 SVG) | Low | ⏳ Planned | Inline SVG data URI in both demo-wall/index.html and the storefront template |
| 10 | Demo Wall kiosk mode (`?kiosk=1`) | Low | ⏳ Planned | CSS only — hides header/footer for TV display |
| 11 | KEDA autoscaler card in Demo Wall | Low | ✅ Done | `get_keda_status()` in server.py; card hidden on non-KEDA branches; replica bar + Active/Idle state |
| 12 | Storefront "Refresh Trace" button | Low | ⏭️ Skipped | Covered by #1 (checkout already shows fresh trace) |
| 13 | `scenario/node-failure` — infra resilience demo | Med | ✅ Done | Node Health card + pod placement sub-rows in Demo Wall; 2-replica+anti-affinity overlay; PDBs |

---

## Architecture decisions

| Decision | Rationale |
|---|---|
| Trace link uses `JAEGER_QUERY_URL` env var | Avoids hardcoding cluster-specific URLs; gracefully degrades to copy-to-clipboard if unset |
| Scenario intent lives in `server.py` (not Git) | `SCENARIO_META` dict is a code constant — no YAML to maintain per branch |
| DEMO-GUIDE.md supersedes RUNBOOK/QUICKSTART/COMMANDS | Operators should not have to jump between files during a live demo |
| Gatekeeper stays `dryrun` on main and all existing branches | Avoids accidental admission blocks; `scenario/policy-enforce` will add the deny story explicitly |
| v1 = blue accent, v2 = green accent (both dark theme) | Blue = "stable/GA", Green (Atlantis) = "canary/new" — tells the versioning story visually |
