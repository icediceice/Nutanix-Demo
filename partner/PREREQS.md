# Prereqs

## Required
- NKP cluster attached and reachable
- Flux controllers running
- Istio + Kiali + Grafana/Loki + Jaeger available
- Access to this repo from cluster
- Flux `helm-controller` available (required for Gatekeeper auto-install)

## Required repo variables
- `clusters/rx-demo/flux/gitrepository.yaml`:
  - `spec.url`
  - `spec.ref.branch` (set desired scenario branch)

## Optional
- `platform/nkp-apps/*`: workspace-scoped AppDeployment templates
- `clusters/rx-demo/image-automation/*`: optional v2 image auto-update
