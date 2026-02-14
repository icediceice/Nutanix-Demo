# NKP Rx GitOps Demo Specification

## 1. Purpose
Provide a branch-driven, repeatable partner demo for NKP Rx that shows:
- GitOps operations with Flux
- Progressive delivery with Istio canary routing
- Incident simulation and observability triage
- Governance posture with Gatekeeper policy in audit mode
- Audience-facing KPI visibility through the Demo Wall

This spec reflects the current repository content in `C:\Git\Nutanix-Demo`.

## 2. Demo Goals
- Demonstrate change control by switching Flux Git source branch, not live-editing YAML.
- Show safe canary rollout from `v1` to `v2` using weighted traffic.
- Prove incident detection and recovery using Kiali, Jaeger, Grafana, and Loki.
- Show policy guardrails and compliance status without blocking the session.
- End every session in a safe low-cost state (`scenario/load-off`).

## 3. Scope By Folder
- `clusters/rx-demo/flux`: Flux source and reconciliation chain (`platform -> apps -> mesh -> ops-loadgen`) plus optional suspended `image-automation`.
- `clusters/rx-demo/image-automation`: Optional Flux image scanning/policy/automation for v2 manifests (Setters strategy).
- `platform`: Namespaces, RBAC, quotas/limits, Gatekeeper Helm install, dry-run policy constraints, optional NKP `AppDeployment` templates.
- `apps`: `otel-shop-lite` service manifests, v1/v2 deployments, incident overlays, and Python app source.
- `mesh`: Istio `DestinationRule` and `VirtualService` overlays for traffic weights and optional mirroring.
- `ops`: k6 load generator base and overlays (`baseline`, `peak`, `off`).
- `prereqs`: Required/optional/sensitive template grouping and guidance.
- `partner`: Operator runbooks, scenario matrix, command sheet, reset/troubleshooting, KPI notes, Demo Wall assets.
- `docs`: Runbook and verification checklist used for preflight and live operation.
- `WOW.md`: KPI/policy objective definition for audience impact.

## 4. Reference Architecture
1. Flux watches repo branch configured in `clusters/rx-demo/flux/gitrepository.yaml`.
2. Flux applies `platform` first, then `apps`, then `mesh`, then `ops-loadgen`.
3. Application runs in `demo-app` namespace with frontend, catalog, checkout, payment services (v1 and v2).
4. Istio routes `frontend` service traffic across subsets `v1` and `v2`.
5. k6 in `demo-ops` continuously drives storefront and checkout traffic.
6. OpenTelemetry traces go to Jaeger collector; app exposes Prometheus metrics and JSON logs with trace IDs.
7. Gatekeeper audits policy conformance (labels, resources, no `:latest`) in demo namespaces.
8. Demo Wall polls Kubernetes read-only and renders branch, readiness, canary, policy, and KPI cards.

## 5. Application and Telemetry Design
- Services: `frontend`, `catalog-api`, `checkout-api`, `payment-mock`.
- Deployment model: both `v1` and `v2` deployed simultaneously; Istio controls user-visible mix.
- Fault injection: `payment-mock-v2` env patch overlays:
  - `normal`: `FAIL_MODE=ok`
  - `incident-latency`: `FAIL_MODE=latency`, `LATENCY_MS=1000`
  - `incident-error`: `FAIL_MODE=error`, `ERROR_RATE=0.10`
- Observability behavior from `apps/otel-shop-lite/src/shared_app.py`:
  - OTLP export to Jaeger collector
  - Prometheus counters/histograms
  - Structured logs including `trace_id` and `span_id`
  - HTTP response headers include trace/span IDs

## 6. Platform Guardrails
- Namespaces: `demo-app`, `demo-ops`; Istio injection enabled on `demo-app`.
- RBAC:
  - `demo-dev-role` in `demo-app`
  - `demo-ops-role` in `demo-app` and `demo-ops`
  - Bindings for groups `demo-devs` and `demo-ops`
- Quotas/limits:
  - `demo-app`: up to 40 pods, 4 CPU requests / 8 CPU limits, 4Gi / 8Gi memory
  - `demo-ops`: up to 20 pods, 2 CPU requests / 4 CPU limits, 2Gi / 4Gi memory
- Gatekeeper:
  - Installed via Flux HelmRelease (`gatekeeper-system`, chart `3.*`)
  - Constraints are `enforcementAction: dryrun` for non-blocking demos
- Policy bundle in `platform/policy/demo-guardrails.yaml`:
  - Required labels: `app`, `version`
  - Required resource requests/limits
  - Disallow `:latest` tag

## 7. Traffic and Load Controls
- Istio baseline starts at `weight-0` overlay (100% v1 / 0% v2).
- Canary overlays:
  - `weight-10` (90/10)
  - `weight-50` (50/50)
  - `weight-100` (0/100)
- Optional mirror overlay: mirror 100% v1 traffic to v2 without serving v2 responses.
- Loadgen overlays:
  - `baseline`: 5 VUs, 30m
  - `peak`: 20 VUs, 30m and higher resources
  - `off`: replicas `0`

## 8. Scenario Model (Branch-Driven)
Branch switching is the demo control plane (`partner/SCENARIOS.md`):
- `scenario/baseline`: normal app, weight-0, baseline load
- `scenario/load-off`: normal app, weight-0, load off
- `scenario/load-peak`: normal app, weight-0, peak load
- `scenario/canary-10`: normal app, weight-10, baseline load
- `scenario/canary-50`: normal app, weight-50, baseline load
- `scenario/canary-100`: normal app, weight-100, baseline load
- `scenario/incident-latency`: latency fault, weight-10, baseline load
- `scenario/incident-error`: error fault, weight-10, baseline load
- `scenario/mirror-v2`: optional mirror mode, baseline load

## 9. Demo Wall and KPI Contract
Demo Wall (`partner/demo-wall`) refreshes every 5 seconds and shows:
- Scenario branch, Flux artifact revision, GitRepository readiness
- Flux Kustomization readiness table
- Loadgen desired/ready replicas
- Canary weights (v1/v2)
- Policy summary (pass/warn/fail/error)
- KPI cards:
  - Flux Success Rate (good >= 90, warn >= 70, bad < 70)
  - Canary Weight v2 (informational)
  - Policy Compliance (good >= 95, warn >= 60, bad < 60 in implementation)
  - Rollback SLA Target (`< 3 minutes`, target card)

## 10. End-to-End Demo Script
1. Preflight:
   - Validate prereqs (`partner/PREREQS.md`, `docs/verification-checklist.md`).
   - Set Flux repo URL/branch via `partner/COMMANDS.md`.
2. Baseline:
   - Run `scenario/baseline`; confirm healthy app and baseline traffic.
3. Progressive delivery:
   - Move through canary branches (`10 -> 50 -> optional 100`) and show visual shift.
4. Incident drill:
   - Switch to latency or error scenario.
   - Show impact path in Kiali -> traces in Jaeger -> metrics in Grafana -> logs in Loki.
5. Governance:
   - Show Gatekeeper present and policy compliance summary in Demo Wall.
   - Optionally show sample violation manifest from `platform/policy/examples`.
6. Recovery:
   - Return to normal overlay and safe canary state.
   - End on `scenario/load-off`.

## 11. Operational Commands and Recovery
- Primary operator command pack: `partner/COMMANDS.md`.
- Reset methods:
  - Fast reset: branch to baseline + reconcile.
  - Hard reset: delete `demo-app` and `demo-ops`, let Flux recreate.
- Troubleshooting: `partner/TROUBLESHOOTING.md`.

## 12. Acceptance Criteria
- Flux applies the chain with `Ready=True` for `platform`, `apps`, `mesh`, `ops-loadgen`.
- Frontend is reachable and generates checkout flow traffic.
- Canary branch changes produce expected v1/v2 weight changes.
- Incident branches produce observable latency/error signals.
- Policy constraints are visible and audit-only (no admission blocking).
- Demo Wall presents branch, health, policy summary, and all KPI cards.
- Session ends with load disabled (`scenario/load-off`).

## 13. In-Scope vs Optional
- In-scope default:
  - Branch-driven scenario transitions
  - Platform + app + mesh + loadgen bundle
  - Gatekeeper audit-mode policy
  - Demo Wall KPI surface
- Optional:
  - Image automation (`clusters/rx-demo/image-automation`)
  - NKP `AppDeployment` templates (`platform/nkp-apps`)
  - Mirroring demo path (`scenario/mirror-v2`)
  - Sensitive template patterns under `prereqs/sensitive-templates`

## 14. Notes and Repository Hygiene
- `apps/otel-shop-lite/src/services/__pycache__` contains generated `.pyc` files and is not part of desired source-of-truth behavior.
- File `nul` exists at repo root and appears unrelated to demo operation.
