# NKP Platform AppDeployment templates

These templates are optional and intentionally not referenced by `platform/kustomization.yaml` by default.

Use these when your Rx reservation supports workspace-scoped `AppDeployment` resources.
Update:
- namespace (workspace namespace)
- `appRef.name` to exact available ClusterApp version
- values ConfigMap content per environment