# Gatekeeper Auto-Install

Gatekeeper is installed automatically by Flux via Helm.

## Resources
- `helmrepository.yaml`: Gatekeeper chart repository
- `helmrelease.yaml`: installs Gatekeeper chart into namespace `gatekeeper-system`
- `namespace.yaml`: ensures target namespace exists

## Notes
- Chart version uses `3.*` to stay on a stable major stream.
- If your Flux installation does not include helm-controller, this release will not reconcile.
