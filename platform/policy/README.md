# Demo Policy Gate

Gatekeeper dry-run policy bundle for demo namespaces.

## Included
- `demo-guardrails.yaml` with:
  - `K8sDemoRequiredLabels` (`app` + `version`)
  - `K8sDemoRequiredResources` (requests/limits)
  - `K8sDemoNoLatest` (blocks `:latest` in dry-run)

## Safety mode
- `enforcementAction: dryrun` on all constraints to avoid blocking live demos.
- Gatekeeper is auto-installed from `platform/gatekeeper` by Flux.

## Optional violation sample
- `examples/policy-violation-example.yaml`
- This file is intentionally not part of kustomize resources.
