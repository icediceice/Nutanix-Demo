# NKP Rx GitOps Demo (Partner Kit)

Simplified, branch-driven demo for NKP Rx environments.

## Recommended workflow (ArgoCD)
1. Install ArgoCD with `clusters/rx-demo/argocd/bootstrap`.
2. Create ArgoCD resources from `clusters/rx-demo/argocd/apps`.
3. Switch scenarios by changing the ArgoCD Application `targetRevision` to a `scenario/*` branch.
4. End on `scenario/load-off`.

## Legacy workflow (Flux)
Flux bootstrap still exists at `clusters/rx-demo/flux`.

## Start here
- `partner/RUNBOOK.md`
- `partner/QUICKSTART.md`
- `partner/SCENARIOS.md`
- `partner/PREREQS.md`
- `partner/TROUBLESHOOTING.md`
- `partner/RESET.md`

## Repo layout
- `clusters/rx-demo/argocd`: ArgoCD bootstrap + Application (recommended)
- `clusters/rx-demo/flux`: Flux source + Kustomization dependency chain (legacy)
- `platform`: namespaces, RBAC, quotas, Istio injection labels, Kommander add-ons
- `apps`: otel-shop-lite app manifests and fault overlays
- `mesh`: Istio DestinationRule/VirtualService overlays
- `ops`: k6 load generator overlays + in-cluster Demo Wall
- `prereqs`: required/optional/sensitive template grouping
- `partner`: operator-facing docs

## Defaults on `main`
- App overlay: normal
- Mesh overlay: weight-0
- Load overlay: baseline
- Image automation Kustomization: suspended by default

## Variables to set before first cluster run
- ArgoCD mode: none (choose a `scenario/*` branch by setting Argo `targetRevision`).
- Flux mode:
  - `clusters/rx-demo/flux/gitrepository.yaml`: set `spec.url` and `spec.ref.branch`.
