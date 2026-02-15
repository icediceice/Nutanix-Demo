# NKP Rx GitOps Demo (Partner Kit)

Simplified, branch-driven demo for NKP Rx environments.

## Partner-first workflow
1. Bootstrap Flux with `clusters/rx-demo/flux`.
2. Select a `scenario/*` branch.
3. Reconcile and demo observability/canary behavior.
4. End on `scenario/load-off`.

No live YAML edits are required during demo sessions.

## Start here
- `partner/QUICKSTART.md`
- `partner/SCENARIOS.md`
- `partner/PREREQS.md`
- `partner/TROUBLESHOOTING.md`
- `partner/RESET.md`
## Alternative: ArgoCD (UI-first CD status)

If you want a clearer CD status UI than Flux, use ArgoCD:
- Install: `clusters/rx-demo/argocd/bootstrap`
- App definitions: `clusters/rx-demo/argocd/apps`
- Branch-driven scenarios remain `scenario/*` (Argo `targetRevision`).


## Repo layout
- `clusters/rx-demo/flux`: Flux source + Kustomization dependency chain
- `platform`: namespaces, RBAC, quotas, Istio injection labels
- `apps`: otel-shop-lite app manifests and fault overlays
- `mesh`: Istio DestinationRule/VirtualService overlays
- `ops`: k6 load generator overlays
- `prereqs`: required/optional/sensitive template grouping
- `partner`: operator-facing docs

## Defaults on `main`
- App overlay: normal
- Mesh overlay: weight-0
- Load overlay: baseline
- Image automation Kustomization: suspended by default

## Variables to set before first cluster run
- `clusters/rx-demo/flux/gitrepository.yaml`
  - `spec.url`
  - `spec.ref.branch` (use a `scenario/*` branch)
- image repositories if needed:
  - `clusters/rx-demo/image-automation/imagerepositories.yaml`