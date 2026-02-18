# Repo Architecture (Load On Demand)

This file is the canonical architecture overview for this git repo.

To avoid token waste:
- Use the section list below. Load only the section(s) you need.
- For deep detail, prefer opening the referenced docs rather than reading unrelated sections here.

## Sections
- 1. What This Repo Is
- 2. Control Plane Model (Branch-Driven GitOps)
- 3. Composition (Kustomize Layout)
- 4. Scenario Model (What Changes Per Branch)
- 5. Key Components (App, Mesh, Load, Policies, Demo Wall)
- 6. Common Change Recipes (Where To Edit)
- 7. Guardrails / Gotchas
- 8. Further References

## 1. What This Repo Is
Nutanix NKP Rx GitOps demo repository. It is designed to be operated by switching branches (for example, `scenario/baseline` to `scenario/incident-error`) rather than editing live manifests in-cluster.

Primary operator entrypoint:
- Complete operator guide (setup, demo flow, commands): `docs/DEMO-GUIDE.md`

## 2. Control Plane Model (Branch-Driven GitOps)
The demo is controlled by ArgoCD:
- ArgoCD Application: `clusters/rx-demo/argocd/apps/application.yaml` (name: `rx-demo`)
- It points at this repo and a `scenario/*` branch via `spec.source.targetRevision`.
- Bootstrapping is handled by `scripts/bootstrap-demo.sh` (installs ArgoCD, creates the Application, points to a scenario branch).

Operational rule: switch scenarios by changing `targetRevision`, not by editing YAML in the cluster.

## 3. Composition (Kustomize Layout)
ArgoCD applies a single Kustomize root:
- Root path: `clusters/rx-demo/argocd/root/kustomization.yaml`
- It composes four top-level “modules”:
  - `platform/` (namespaces, RBAC, quotas, policy, optional platform add-ons)
  - `apps/` (otel-shop-lite manifests and overlays)
  - `mesh/` (Istio Gateway/VirtualService/DestinationRule and overlays)
  - `ops/` (load generator + Demo Wall and overlays)

Each module is itself Kustomize-driven and typically selects one overlay by referencing it from that module’s `kustomization.yaml`.

## 4. Scenario Model (What Changes Per Branch)
`scenario/*` branches represent a demo state. The common pattern is:
- Keep base manifests stable.
- Change which overlay is selected in:
  - `apps/otel-shop-lite/kustomization.yaml`
  - `mesh/istio/kustomization.yaml`
  - `ops/loadgen/kustomization.yaml`

Examples of what scenarios do:
- Canary: change Istio weight overlays (10/50/100).
- Incidents: apply app overlays that inject latency/errors (typically on payment-mock v2).
- Load: switch loadgen overlays (baseline/peak/off).
- Optional: KEDA scenario installs KEDA resources and uses a Prometheus endpoint ConfigMap (see `platform/keda` and `docs/keda.md`).

Canonical scenario list: `docs/DEMO-GUIDE.md §4`.

## 5. Key Components (App, Mesh, Load, Policies, Demo Wall)
Load only the subtopic you need:

### 5.1 Application (otel-shop-lite)
- Manifests and overlays: `apps/otel-shop-lite/`
- Service source (minimal Python): `apps/otel-shop-lite/src/`
- Versioned manifests: `apps/otel-shop-lite/versions/v1`, `apps/otel-shop-lite/versions/v2`

### 5.2 Mesh (Istio)
- Base gateway/routing resources: `mesh/istio/`
- Traffic shaping overlays: `mesh/istio/overlays/` (weights, optional mirroring)

### 5.3 Ops (Loadgen + Demo Wall)
- Load generator: `ops/loadgen/` with overlays under `ops/loadgen/overlays/`
- Demo Wall (in-cluster): `ops/demo-wall/`
- Demo Wall (local standalone): `ops/demo-wall-local/`

### 5.4 Platform Guardrails
- Namespaces/RBAC/quotas: `platform/`
- Gatekeeper policy bundle: `platform/policy/` (typically audit/dry-run for demos)

## 6. Common Change Recipes (Where To Edit)
Load only the recipe you need:

### 6.1 Add A New Scenario
Typical approach:
1. Create a new `scenario/<name>` branch.
2. Add/adjust overlays as needed under `apps/otel-shop-lite/overlays/`, `mesh/istio/overlays/`, `ops/loadgen/overlays/`.
3. Point the module selector files at your overlay:
   - `apps/otel-shop-lite/kustomization.yaml`
   - `mesh/istio/kustomization.yaml`
   - `ops/loadgen/kustomization.yaml`
4. Update the scenario table: `docs/DEMO-GUIDE.md §4`.

### 6.2 Change Canary Weights
- Edit or add Istio overlay under `mesh/istio/overlays/`.
- Ensure `mesh/istio/kustomization.yaml` selects the intended overlay in the scenario branch.

### 6.3 Change Load Profile
- Edit or add overlay under `ops/loadgen/overlays/`.
- Ensure `ops/loadgen/kustomization.yaml` selects the intended overlay in the scenario branch.

### 6.4 Add Or Adjust Policy Checks
- Policy lives under `platform/policy/`.
- For demos, prefer non-blocking settings (audit/dry-run) unless explicitly asked to enforce.

## 7. Guardrails / Gotchas
- Do not merge `scenario/*` branches into `main`. They are intended demo runtime states.
- Avoid running multiple GitOps controllers against the same demo resources/namespaces.
- Never commit kubeconfigs or secrets. `auth/` is intentionally ignored by git.
- When editing Kustomize, keep `kustomization.yaml` paths valid and consistent with the scenario model.

## 8. Further References
- Full specification (more detailed than this doc): `docs/demo-spec.md`
- Pre-flight / day-before checklist: `docs/verification-checklist.md`
- KEDA autoscaling notes: `docs/keda.md`
- Complete operator guide (setup, demo flow, commands): `docs/DEMO-GUIDE.md`

