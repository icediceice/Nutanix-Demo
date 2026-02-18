# NKP Rx GitOps Demo (Partner Kit)

Simplified, branch-driven demo for NKP Rx environments.

## Recommended workflow (ArgoCD)
0. `git clone https://github.com/icediceice/Nutanix-Demo.git` and `cd Nutanix-Demo`
1. Bootstrap everything (incl. ArgoCD) with `./scripts/bootstrap-demo.sh`.
2. Switch scenarios by changing the ArgoCD Application `targetRevision` to a `scenario/*` branch.
3. End on `scenario/load-off`.

## Start here
- `partner/DEMO-GUIDE.md` ← **start here** — complete operator guide (setup → demo flow → commands)
- `partner/NKP-CONSOLE-GUIDE.md` ← which features to show in the NKP console vs Demo Wall
- `partner/PREREQS.md`
- `partner/TROUBLESHOOTING.md`
- `partner/RESET.md`
- `PROGRESS.md` ← improvement backlog and session log

KEDA (optional autoscaling demo):
- `docs/keda.md`

## Repo layout
- `clusters/rx-demo/argocd`: ArgoCD bootstrap + Application (recommended)
- `platform`: namespaces, RBAC, quotas, Istio injection labels, Kommander add-ons
- `apps`: otel-shop-lite app manifests and fault overlays
- `mesh`: Istio DestinationRule/VirtualService overlays
- `ops`: k6 load generator overlays + in-cluster Demo Wall
- `prereqs`: required/optional/sensitive template grouping
- `partner`: operator-facing docs

## Defaults on `main`
- App overlay: normal
- Mesh overlay: weight-0
- Load overlay: baseline
- Image automation Kustomization: suspended by default

## Variables to set before first cluster run
- ArgoCD mode: none (choose a `scenario/*` branch by setting Argo `targetRevision`).
Note: Kommander uses internal GitOps controllers; the demo is operated via ArgoCD.
