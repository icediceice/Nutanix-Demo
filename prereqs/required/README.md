# Required Prereqs

This is the minimum required cluster-state bundle for this demo.

Includes:
- platform namespaces, rbac, quotas, istio labels
- demo apps
- mesh routing
- loadgen resources

Apply through Flux Kustomization chain for deterministic ordering.