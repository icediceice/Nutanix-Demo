# ArgoCD Quickstart (NKP Rx Demo)

This repo supports two GitOps modes:
- Flux (original): `clusters/rx-demo/flux`
- ArgoCD (status-first): `clusters/rx-demo/argocd`

## Preconditions
- You are deploying to a Kommander-managed workload cluster.
- Do not run the demo via Flux and ArgoCD at the same time on the same cluster.

## Install ArgoCD
```bash
kubectl apply -k clusters/rx-demo/argocd/bootstrap
```

## Create the Demo Application
```bash
kubectl apply -f clusters/rx-demo/argocd/apps/appproject.yaml
kubectl apply -f clusters/rx-demo/argocd/apps/application.yaml
```

## Access ArgoCD UI
If your cluster supports LoadBalancers, `argocd-server` will get an external IP:
```bash
kubectl -n argocd get svc argocd-server -o wide
```

Fallback (always works):
```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```
Open `https://localhost:8080`.

Login:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d && echo
```
Username is `admin`.

## Switch Scenario (Branch-Driven)
In ArgoCD UI, edit `rx-demo` and set `targetRevision` to another `scenario/*` branch.

Examples:
- `scenario/baseline`
- `scenario/canary-10`
- `scenario/incident-latency`
- `scenario/load-off`
