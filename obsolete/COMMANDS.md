# Partner Command Sheet (ArgoCD)

Use this for operator copy/paste during demos.

## Print all access points (recommended)
```bash
./scripts/print-access.sh --kubeconfig auth/workload02.conf
```

If Kommander is only on the management cluster, add:
```bash
./scripts/print-access.sh --kubeconfig auth/workload02.conf --mgmt-kubeconfig auth/management.conf
```

## Prereqs
- `kubectl` points to the target workload cluster.
- ArgoCD installed (`argocd` namespace).

## Check status (primary)
```bash
kubectl -n argocd get application rx-demo -o wide
kubectl -n demo-ops get deploy demo-loadgen
kubectl -n demo-ops get svc demo-wall -o wide
```

## ArgoCD UI access
```bash
kubectl -n argocd get svc argocd-server -o wide
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d && echo
```

## Switch scenario branch (ArgoCD)
Replace `<branch>` with one of:
- `scenario/baseline`
- `scenario/load-off`
- `scenario/load-peak`
- `scenario/canary-10`
- `scenario/canary-50`
- `scenario/canary-100`
- `scenario/incident-latency`
- `scenario/incident-error`
- `scenario/mirror-v2`

```bash
kubectl -n argocd patch application rx-demo --type merge \
  -p "{\"spec\":{\"source\":{\"targetRevision\":\"<branch>\"}}}"
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
kubectl -n argocd get application rx-demo -o wide
```

## Resource Quotas (Beat 2 — Kommander → Namespaces)
```bash
kubectl describe resourcequota demo-app-quota -n demo-app
kubectl describe resourcequota demo-ops-quota -n demo-ops
kubectl describe limitrange default-limits -n demo-app
```

## RBAC (Beat 3 — Kommander → Access Control)
```bash
kubectl get roles -n demo-app -o wide
kubectl get rolebindings -n demo-app -o wide
```

## Platform Add-ons (Beat 4 — Kommander → Applications)
```bash
kubectl get appdeployments -A 2>/dev/null || \
  kubectl get helmreleases -n kommander-default-workspace -o wide
```

## Governance (Gatekeeper) quick checks
```bash
kubectl get constrainttemplates.templates.gatekeeper.sh
kubectl get constraints -A | rg demo- || true
```

Optional (non-blocking violation example):
```bash
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
kubectl -n demo-app get pod policy-violation-example -o wide
kubectl get k8sdemorequiredlabels.constraints.gatekeeper.sh demo-required-labels -o jsonpath='{.status.totalViolations}{"\n"}' || true
kubectl get k8sdemorequiredresources.constraints.gatekeeper.sh demo-required-resources -o jsonpath='{.status.totalViolations}{"\n"}' || true
kubectl get k8sdemonolatest.constraints.gatekeeper.sh demo-no-latest -o jsonpath='{.status.totalViolations}{"\n"}' || true
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

## Demo app access (external)
```bash
kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway -o wide
```
Open: `http://<ISTIO_INGRESS_LB_IP>/`

## Fallback port-forwards
```bash
kubectl -n demo-app port-forward svc/frontend 8080:80
kubectl -n demo-ops port-forward svc/demo-wall 9090:80
kubectl -n argocd port-forward svc/argocd-server 8081:443
```
