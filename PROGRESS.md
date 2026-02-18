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

---

## Architecture decisions

| Decision | Rationale |
|---|---|
| Trace link uses `JAEGER_QUERY_URL` env var | Avoids hardcoding cluster-specific URLs; gracefully degrades to copy-to-clipboard if unset |
| Scenario intent lives in `server.py` (not Git) | `SCENARIO_META` dict is a code constant — no YAML to maintain per branch |
| DEMO-GUIDE.md supersedes RUNBOOK/QUICKSTART/COMMANDS | Operators should not have to jump between files during a live demo |
| Gatekeeper stays `dryrun` on main and all existing branches | Avoids accidental admission blocks; `scenario/policy-enforce` will add the deny story explicitly |
| v1 = blue accent, v2 = green accent (both dark theme) | Blue = "stable/GA", Green (Atlantis) = "canary/new" — tells the versioning story visually |
