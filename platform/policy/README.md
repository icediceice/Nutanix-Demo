# Demo Policy Gate

Kyverno audit-only policy bundle for demo namespaces.

## Included
- `demo-guardrails.yaml` with:
  - required `app` + `version` labels
  - required requests/limits
  - disallow `:latest` image tags

## Safety mode
- `validationFailureAction: Audit` to avoid blocking live demos.

## Optional violation sample
- `examples/policy-violation-example.yaml`
- This file is intentionally not part of kustomize resources.
