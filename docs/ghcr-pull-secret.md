# GHCR Image Pull Secret (Demo App Images)

The demo app manifests reference images under `ghcr.io/icediceice/otel-shop-lite-*`.
If these images are private, Kubernetes will fail to pull them without credentials.

This repo expects a Docker registry pull secret named `ghcr-pull` in the `demo-app` namespace.

Notes:
- The token needs at least `read:packages` to pull (and `write:packages` if you are pushing images).
- Do not commit kubeconfigs/tokens to git.

## Option A: Use GitHub CLI (Recommended)

Login:

```bash
gh auth login
```

Then create/update the secret (idempotent):

```bash
export GHCR_USERNAME="icediceice"
export GHCR_TOKEN="$(gh auth token)"

kubectl -n demo-app create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username="${GHCR_USERNAME}" \
  --docker-password="${GHCR_TOKEN}" \
  --docker-email="unused@example.com" \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Create Secret (Bash)

```bash
kubectl -n demo-app create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username="<GHCR_USERNAME>" \
  --docker-password="<GHCR_TOKEN>" \
  --docker-email="unused@example.com"
```

## Restart Deployments

```bash
kubectl -n demo-app rollout restart \
  deploy/frontend-v1 deploy/frontend-v2 \
  deploy/catalog-api-v1 deploy/catalog-api-v2 \
  deploy/checkout-api-v1 deploy/checkout-api-v2 \
  deploy/payment-mock-v1 deploy/payment-mock-v2
```
