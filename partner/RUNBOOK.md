# Partner Runbook (ArgoCD + In-Cluster Demo Wall)

This demo is branch-driven. You do not edit live YAML in the cluster during the session.

## 0) Rules (avoid conflicts)
- Use **ArgoCD** to deploy the demo (recommended).
- Do **not** run another GitOps controller to manage the same demo namespaces/resources on the same cluster.
- The workload cluster should be attached to Kommander so platform add-ons (Istio/Kiali/Jaeger) can be installed.

## 1) Deploy To A New Cluster
### 1.0 Clone repo + kubeconfig
```bash
git clone https://github.com/icediceice/Nutanix-Demo.git
cd Nutanix-Demo
mkdir -p auth
```

Place your workload cluster kubeconfig at:
- `auth/workload02.conf`

Sanity check:
```bash
kubectl --kubeconfig auth/workload02.conf get nodes
```

Point `kubectl` at the target workload cluster (example: `workload02`).

### 1.1 One-command bootstrap (recommended)
This handles new-cluster gaps (enables Istio/Kiali/Jaeger via Kommander AppDeployment if available, installs ArgoCD, creates the ArgoCD Application, and points it at a `scenario/*` branch):

Recommended (explicit kubeconfig):
```bash
./scripts/bootstrap-demo.sh --kubeconfig auth/workload02.conf --branch scenario/load-off
```

If your `kubectl` context is already set to the workload cluster, you can omit `--kubeconfig`:
```bash
./scripts/bootstrap-demo.sh --branch scenario/load-off
```

### 1.2 Manual bootstrap (fallback)
```bash
kubectl apply -k clusters/rx-demo/argocd/bootstrap
kubectl -n argocd rollout status deploy/argocd-server --timeout=300s
kubectl apply -f clusters/rx-demo/argocd/apps/appproject.yaml
kubectl apply -f clusters/rx-demo/argocd/apps/application.yaml
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/load-off"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Get ArgoCD UI address:
```bash
kubectl -n argocd get svc argocd-server -o wide
```

Get initial admin password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d && echo
```

Login:
- URL: `https://<ARGOCD_LB_IP>/`
- Username: `admin`
- Password: output from command above

Expected: `rx-demo` becomes `Synced` and `Healthy` on branch `scenario/load-off`.

## 2) Access The Demo App (External)
This repo configures an Istio Gateway/VirtualService so you can access the frontend via the ingress IP.

Get Istio ingress external IP:
```bash
kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide
```

Open:
- `http://<ISTIO_INGRESS_LB_IP>/`

Fallback (no LoadBalancer):
```bash
kubectl -n demo-app port-forward svc/frontend 8080:80
```
Open `http://localhost:8080`.

## 3) Access Demo Wall (In-Cluster)
Demo Wall is deployed by ArgoCD into `demo-ops` as `svc/demo-wall` (LoadBalancer).

```bash
kubectl -n demo-ops get svc demo-wall -o wide
```

Open:
- `http://<DEMO_WALL_LB_IP>/`

Fallback (no LoadBalancer):
```bash
kubectl -n demo-ops port-forward svc/demo-wall 9090:80
```
Open `http://localhost:9090`.

## 4) Switch Scenarios (Branch-Driven)
Change the ArgoCD Application `targetRevision` to a `scenario/*` branch.

Example: canary 10%
```bash
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"scenario/canary-10"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
kubectl -n argocd get application rx-demo -o wide
```

Branches:
- `scenario/baseline`
- `scenario/load-off`
- `scenario/load-peak`
- `scenario/canary-10`
- `scenario/canary-50`
- `scenario/canary-100`
- `scenario/incident-latency`
- `scenario/incident-error`
- `scenario/mirror-v2`

## 5) End Session Safely
Always end on:
- `scenario/load-off`

## 6) Reset
Fast reset:
- set `targetRevision` to `scenario/baseline`, wait `Synced/Healthy`, then set `scenario/load-off`.

Hard reset (rare):
```bash
kubectl delete ns demo-app demo-ops
```
ArgoCD will recreate them on next sync.
