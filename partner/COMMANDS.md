# Partner Command Sheet

Use this for operator copy/paste during demos.

## Prereqs
- `kubectl` is configured to the target cluster.
- Flux is installed in namespace `flux-system`.

## Set repo URL + starting branch
```powershell
kubectl -n flux-system patch gitrepository nkp-rx-demo --type merge -p "{\"spec\":{\"url\":\"https://github.com/icediceice/Nutanix-Demo.git\",\"ref\":{\"branch\":\"scenario/baseline\"}}}"
```

## Switch scenario branch (single command)
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

```powershell
kubectl -n flux-system patch gitrepository nkp-rx-demo --type merge -p "{\"spec\":{\"ref\":{\"branch\":\"<branch>\"}}}"
```

## Reconcile now (optional, speeds demo)
```powershell
kubectl -n flux-system annotate gitrepository nkp-rx-demo reconcile.fluxcd.io/requestedAt=\"$(Get-Date -Format o)\" --overwrite
kubectl -n flux-system annotate kustomization platform reconcile.fluxcd.io/requestedAt=\"$(Get-Date -Format o)\" --overwrite
kubectl -n flux-system annotate kustomization apps reconcile.fluxcd.io/requestedAt=\"$(Get-Date -Format o)\" --overwrite
kubectl -n flux-system annotate kustomization mesh reconcile.fluxcd.io/requestedAt=\"$(Get-Date -Format o)\" --overwrite
kubectl -n flux-system annotate kustomization ops-loadgen reconcile.fluxcd.io/requestedAt=\"$(Get-Date -Format o)\" --overwrite
```

## Readiness checks
```powershell
kubectl -n flux-system get gitrepository nkp-rx-demo
kubectl -n flux-system get kustomization platform,apps,mesh,ops-loadgen,image-automation
kubectl -n demo-ops get deploy demo-loadgen
kubectl -n demo-app get secret ghcr-pull
kubectl get constrainttemplates.templates.gatekeeper.sh
kubectl get k8sdemorequiredlabels.constraints.gatekeeper.sh demo-required-labels -o jsonpath="{.status.totalViolations}"
```

## Safe end of session
```powershell
kubectl -n flux-system patch gitrepository nkp-rx-demo --type merge -p "{\"spec\":{\"ref\":{\"branch\":\"scenario/load-off\"}}}"
```
