# Prereqs

## Required
- NKP cluster attached and reachable
- Flux controllers running
- Istio + Kiali + Grafana/Loki + Jaeger available
- Access to this repo from cluster
- Gatekeeper installed and running (Kommander typically installs this)
- Image registry access to pull demo app images
  - If `ghcr.io/icediceice/otel-shop-lite-*` images are private, create `secret/ghcr-pull` in `demo-app` (see `docs/ghcr-pull-secret.md`)

## Required repo variables
- `clusters/rx-demo/flux/gitrepository.yaml`:
  - `spec.url`
  - `spec.ref.branch` (set desired scenario branch)

## Optional
- `platform/nkp-apps/*`: workspace-scoped AppDeployment templates
- `clusters/rx-demo/image-automation/*`: optional v2 image auto-update
