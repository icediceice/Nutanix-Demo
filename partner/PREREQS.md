# Prereqs (ArgoCD)

## Required
- NKP workload cluster attached and reachable
- Kommander components healthy
  - Flux controllers for Kommander internals typically run in `kommander-flux`
- ArgoCD installed in `argocd` namespace (this demo deploys via ArgoCD)
- Istio + Kiali + Grafana/Loki + Jaeger available (Kommander-managed workload add-ons)
- Gatekeeper installed and running
- Image registry access to pull demo images
  - If `ghcr.io/icediceice/otel-shop-lite-*` images are private, create `secret/ghcr-pull` in `demo-app` (see `docs/ghcr-pull-secret.md`)

## Required repo inputs
- ArgoCD deploy entrypoint: `clusters/rx-demo/argocd/root`
- Scenario control is via `scenario/*` branches (ArgoCD `Application.spec.source.targetRevision`)

## Optional
- `clusters/rx-demo/image-automation/*`: optional v2 image auto-update (Flux image automation pattern)
- `platform/nkp-apps/*`: workspace-scoped AppDeployment templates
