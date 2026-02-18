# NKP GitOps Demo — Complete Operator Guide

Single source of truth for running the NKP Rx demo end-to-end.
Open this file before the demo and keep it on your second screen.

---

## 0. Prerequisites (check before every session)

| Requirement | Verify with |
|---|---|
| `kubectl` pointing at the workload cluster | `kubectl get nodes` |
| Cluster kubeconfig at `auth/workload02.conf` | `ls auth/` |
| Git repo cloned | `git log --oneline -1` |
| Istio, Kiali, Jaeger, Grafana installed | `kubectl get ns` — look for `istio-system`, `kommander-default-workspace` |
| Enough resources | `kubectl describe quota -n demo-app` — pods < 35 of 40 |

Full prerequisites: `docs/PREREQS.md`

---

## 1. Bootstrap (first time only)

```bash
./scripts/bootstrap-demo.sh --kubeconfig auth/workload02.conf --branch scenario/load-off
```

If you also have a management cluster kubeconfig (for Kommander add-ons):
```bash
./scripts/bootstrap-demo.sh \
  --kubeconfig auth/workload02.conf \
  --mgmt-kubeconfig auth/management.conf \
  --branch scenario/load-off
```

Wait for `rx-demo` to become `Synced / Healthy` in ArgoCD, then get your URLs:

```bash
./scripts/print-access.sh --kubeconfig auth/workload02.conf
```

### Your demo URLs (fill in before the room fills up)

| Surface | URL | Credentials |
|---|---|---|
| **Demo Wall** | `http://<DEMO_WALL_LB>/` | — |
| **Storefront** | `http://<ISTIO_INGRESS>/` | — |
| **ArgoCD** | `https://<ARGOCD_LB>/` | admin / see below |
| **Kommander** | `https://<NKP_BASE>/dkp/kommander/dashboard` | SSO |
| **Kiali** | `https://<NKP_BASE>/dkp/kiali` | SSO |
| **Jaeger** | `https://<NKP_BASE>/dkp/jaeger` | SSO |
| **Grafana** | `https://<NKP_BASE>/dkp/logging/grafana` | SSO |

ArgoCD admin password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d && echo
```

Demo Wall credentials are **auto-discovered** from cluster secrets — no manual setup needed:
- ArgoCD password → `argocd/argocd-initial-admin-secret`
- Kommander SSO password → `kommander-default-workspace/dkp-admin-user-password`

Open the Quick Reference page (`/quickref`) after bootstrap to verify all passwords populated correctly.

Fallback port-forwards (no LoadBalancer):
```bash
kubectl -n demo-ops port-forward svc/demo-wall 9090:80          # Demo Wall
kubectl -n demo-app port-forward svc/frontend 8080:80           # Storefront
kubectl -n argocd port-forward svc/argocd-server 8443:443       # ArgoCD
```

---

## 2. Switch scenarios (during the demo)

All scenario changes are made in **ArgoCD** — either via the UI or this command:

```bash
# Replace <branch> with the scenario name (e.g. scenario/canary-10)
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"<branch>"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

The Demo Wall auto-refreshes every 5 s and shows the new branch, its intent,
and a "Next →" hint for the following beat.

---

## 3. Demo flow (complete sequence)

### Beat 1 — Open the Demo Wall and introduce the stack

**Action**: Open the Demo Wall. Set scenario to `scenario/baseline`.

**What the audience sees**:
- Scenario card: `scenario/baseline` — "Stable baseline — 100% traffic to v1"
- CD Status: `Synced / Healthy`
- Traffic: `v1 / v2 = 100 / 0`
- Policy: compliance %

**What you say**: _"This is the NKP GitOps demo. Everything on screen is live — the
Demo Wall pulls from the Kubernetes API every five seconds. The only way to
change the cluster state is to change the Git branch. No kubectl apply, no
live YAML edits."_

---

### Beat 2 — Multi-cluster management (Kommander)

**Action**: Open **Kommander → Clusters**.

**What to show**: The attached workload cluster, version, and health.

**What you say**: _"One Kommander manages every cluster in this environment.
Add a new cluster and it inherits the same policies and add-ons automatically."_

---

### Beat 3 — Platform add-ons (Kommander)

**Action**: **Kommander → Applications** (workspace-scoped tab).

**What to show**: Istio, Kiali, Jaeger, Grafana — all `Deployed`.

**What you say**: _"The entire observability stack was deployed by NKP's app
catalog with a single GitOps commit. No manual Helm installs."_

---

### Beat 4 — Resource quotas (Kommander)

**Action**: **Kommander → Clusters → [workload cluster] → Namespaces → demo-app**.

**What to show**: Live quota usage — pods, CPU request, memory.

Terminal side-by-side:
```bash
kubectl describe resourcequota demo-app-quota -n demo-app
kubectl describe limitrange default-limits -n demo-app
```

**What you say**: _"Every team namespace has a hard quota. A rogue deployment
can't starve the rest of the cluster — the platform enforces guardrails
automatically."_

---

### Beat 5 — RBAC / Access control (Kommander)

**Action**: **Kommander → Access Control → Roles**.

**What to show**: `dev-role-demo-app` (read-only) vs `ops-role-demo-app` (full).

Terminal:
```bash
kubectl get roles -n demo-app -o wide
kubectl get rolebindings -n demo-app -o wide
```

**What you say**: _"Developers can observe their workloads but cannot change
replicas. No one has cluster-admin by default — least-privilege baked in."_

---

### Beat 6 — GitOps in action: start progressive delivery

**Action**: Switch to `scenario/canary-10` in ArgoCD.

Watch the Demo Wall:
- Traffic card changes to `v1 / v2 = 90 / 10`
- CD Status briefly shows `Progressing`, then `Synced / Healthy`
- Intent shows: _"Progressive delivery — 10% traffic shifted to v2"_
- Next hint shows: `canary-50`

**What you say**: _"I changed one line in Git — the branch pointer. ArgoCD
reconciled 12 Kubernetes resources in under 30 seconds. No downtime, no
kubectl apply."_

---

### Beat 7 — Service mesh topology (Kiali)

**Action**: Open **Kiali** (via Kommander SSO or Demo Wall platform link).

**What to show** (with `canary-10` active):
- Live traffic graph: frontend → payment-mock v1 and v2.
- Click the v2 edge: request rate, error rate, latency histogram.

**What you say**: _"Zero custom instrumentation. Istio captures every
request automatically. Kiali shows the topology and health of every
service-to-service call in real time."_

---

### Beat 8 — Ramp the canary

**Action**: Switch to `scenario/canary-50`, then `scenario/canary-100`.

Watch:
- Demo Wall traffic card: 50/50 → 0/100
- Kiali graph updates live

---

### Beat 9 — Policy governance (Gatekeeper)

**Action (ArgoCD side)**: ArgoCD → `rx-demo` → Resources tab → filter `Constraint`.
**Action (Demo Wall side)**: Policy card shows compliance %.

Terminal:
```bash
kubectl get constraints -A

# Live violation demo (non-blocking dryrun):
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
# Watch compliance card drop on Demo Wall
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

**What you say**: _"Policy is just another Kubernetes resource — it lives in
Git, not in someone's head. Gatekeeper audits every object continuously. We're
in dryrun mode today; flip `enforcementAction: deny` and the bad pod is
rejected at admission."_

---

### Beat 10 — Incident drill: inject latency

**Action**: Switch to `scenario/incident-latency`.

Demo Wall shows:
- Traffic: 90/10 (re-split to canary)
- Intent: _"Incident drill — v2 injecting 1 s latency, watch Jaeger traces"_

**In the storefront**: Click `Checkout ×3`. Watch the Activity box show
slower responses. The **Last Trace** badge appears in the bag panel.

If `JAEGER_QUERY_URL` is configured: click **→ Jaeger** to jump directly to
the trace. Otherwise copy the trace ID and paste into Jaeger search.

---

### Beat 11 — Find the root cause in Jaeger

**Action**: Open **Jaeger** (via Demo Wall link or Kommander SSO).

- Service: `frontend` → Search → open the trace from the checkout.
- Expand spans: frontend → checkout-api → payment-mock-v2.
- The payment-mock v2 span shows the 1 s delay highlighted.

**What you say**: _"Every click in the storefront generates a real distributed
trace. We pinpointed exactly which service introduced the latency — without
grepping logs."_

---

### Beat 12 — Rollback

**Action**: Switch back to `scenario/baseline` in ArgoCD.

- Traffic returns to 100/0
- Demo Wall shows Healthy
- Kiali graph normalises

**What you say**: _"Rollback is the same operation as the canary deploy — one
branch change in Git. ArgoCD reconciles in under 30 seconds."_

---

### Beat 13 — End session

**Action**: Switch to `scenario/load-off`.

This stops the load generator. The cluster is idle and safe to leave.

---

### Beat 14 — (Optional) Quota pressure

**Action**: Switch to `scenario/quota-pressure` in ArgoCD.

What happens:
- A `quota-stress` Deployment (20 × `pause` containers) is added to `demo-app`
- Pod count rises to ~75–80% of the 40-pod namespace quota
- Demo Wall **Namespace Quota** card goes amber

Show **Kommander → Clusters → [workload cluster] → Namespaces → demo-app** — the bar goes amber in real time.

Then try to exceed the quota:
```bash
# Attempt to scale quota-stress beyond the limit
kubectl -n demo-app scale deploy quota-stress --replicas=30
# Pod count will exceed quota — new pods stay Pending
kubectl -n demo-app get pods | grep -c Running
kubectl -n demo-app get events --sort-by=.lastTimestamp | tail -5
# Look for: "exceeded quota: demo-app-quota"
```

**What you say**: _"The platform hard-stopped that scale request. No alert, no ticket, no manual intervention —
the quota enforced the contract automatically. Developers get self-service, ops teams get guardrails."_

Return to baseline when done.

---

### Beat 15 — (Optional) Policy enforcement: Gatekeeper deny mode

**Action**: Switch to `scenario/policy-enforce` in ArgoCD.

What changes:
- `K8sDemoRequiredLabels` constraint flips from `dryrun` → `deny`
- Demo Wall policy card stays green (existing workloads are compliant)
- ArgoCD shows the constraint as `Synced / Healthy`

Now apply the violation example:
```bash
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
```

The pod is **rejected at admission** — unlike Beat 9 (dryrun), this one never starts:
```
Error from server ([demo-required-labels] label 'app' is required): ...
```

Show the error message to the audience. Then clean up and confirm nothing changed:
```bash
kubectl -n demo-app get pods | grep policy-violation  # nothing
```

**What you say**: _"That pod never existed. Gatekeeper intercepted the API call before Kubernetes even
scheduled it. One line in Git — `enforcementAction: deny` — is the difference between audit and enforcement.
The policy is the same; the action changed."_

Return to baseline when done.

---

### Beat 16 — (Optional) Autoscaling with KEDA

> Requires KEDA pre-installed (`platform/keda/` applied, or bootstrap with `--branch scenario/keda-checkout`).

**Action**: Switch to `scenario/keda-checkout` in ArgoCD.

What happens:
- ArgoCD syncs the `keda-checkout` overlay — deploys the KEDA `ScaledObject` for `checkout-api-v1`
- Both checkout-api replicas start at **0** (scale-to-zero)
- The Demo Wall **Autoscaler (KEDA)** card appears and shows **"Idle · scaled to zero"** in amber

Wait ~30 s, then watch the storefront checkout under baseline load:
- KEDA detects Istio request rate crossing the threshold (0.2 RPS)
- `checkout-api-v1` scales from 0 → N replicas
- Demo Wall card flips to **"Active ↑ scaling"** in green; the replica bar fills

```bash
# Watch the scale event live
kubectl -n demo-app get deploy checkout-api-v1 -w

# Inspect the ScaledObject trigger and conditions
kubectl -n demo-app describe scaledobject checkout-api-v1-keda
```

**What you say**: _"One branch switch deployed KEDA and gave checkout-api a Prometheus-driven autoscaler.
The platform saw traffic, woke the service from zero, and will scale it back down after the cooldown window —
no HPA YAML, no manual tuning."_

Return to baseline when done:
```bash
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

---

## 4. Scenario reference

| Branch | What it does | Intent (shown in Demo Wall) | Logical next |
|---|---|---|---|
| `scenario/baseline` | Normal app, all v1, baseline load | Stable baseline — 100% traffic to v1 | `canary-10` |
| `scenario/load-off` | Normal app, load disabled | Load off — cluster at rest | `baseline` |
| `scenario/load-peak` | Normal app, high load | Peak load — stress-testing v1 capacity | `baseline` |
| `scenario/canary-10` | 90/10 split, baseline load | Progressive delivery — 10% to v2 | `canary-50` |
| `scenario/canary-50` | 50/50 split, baseline load | Progressive delivery — 50/50 split | `canary-100` |
| `scenario/canary-100` | 0/100 full cutover | Full cutover — 100% traffic on v2 | `incident-latency` |
| `scenario/incident-latency` | v2 adds 1 s latency, 90/10 | Incident drill — v2 injecting latency | `incident-error` |
| `scenario/incident-error` | v2 returns 10% errors, 90/10 | Incident drill — v2 returning errors | `baseline` |
| `scenario/mirror-v2` | Mirror all traffic to v2 silently | Traffic mirroring | `baseline` |
| `scenario/keda-checkout` | KEDA scales checkout-api to zero | Autoscaling — scale to zero | `baseline` |
| `scenario/quota-pressure` | 20 pause-pods fill ~75% pod quota | Quota pressure — guardrails active | `baseline` |
| `scenario/policy-enforce` | Gatekeeper deny on required-labels | Policy enforcement — deny mode | `baseline` |

---

## 5. Quick command reference

### ArgoCD

```bash
# Check app status
kubectl -n argocd get application rx-demo -o wide

# Switch scenario (replace <branch>)
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"<branch>"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

### Cluster state checks

```bash
# Loadgen
kubectl -n demo-ops get deploy demo-loadgen

# Canary weights (Istio VirtualService)
kubectl -n demo-app get virtualservice frontend-ingress -o yaml | grep -A5 weight

# Quotas
kubectl describe resourcequota demo-app-quota -n demo-app
kubectl describe resourcequota demo-ops-quota -n demo-ops

# RBAC
kubectl get roles -n demo-app -o wide
kubectl get rolebindings -n demo-app -o wide

# Platform add-ons
kubectl get appdeployments -A 2>/dev/null || \
  kubectl get helmreleases -n kommander-default-workspace -o wide

# Gatekeeper
kubectl get constraints -A
kubectl get k8sdemorequiredlabels.constraints.gatekeeper.sh \
  demo-required-labels -o jsonpath='{.status.totalViolations}{"\n"}'
```

### Policy violation demo (non-blocking)

```bash
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
kubectl -n demo-app get pod policy-violation-example -o wide
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

### Reset

```bash
# Fast reset
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
# wait Synced/Healthy, then set load-off

# Hard reset (rare)
kubectl delete ns demo-app demo-ops
# ArgoCD recreates them on next sync
```

---

## 6. NKP console navigation (quick reference)

Replace `<NKP_BASE>` with the URL from Demo Wall → Platform Access → Kommander.

| What to show | URL |
|---|---|
| Clusters | `<NKP_BASE>/dkp/kommander/dashboard/clusters` |
| Applications catalog | `<NKP_BASE>/dkp/kommander/dashboard/applications` |
| Access Control / RBAC | `<NKP_BASE>/dkp/kommander/dashboard/access-control` |
| Kiali | `<NKP_BASE>/dkp/kiali` |
| Jaeger | `<NKP_BASE>/dkp/jaeger` |
| Grafana | `<NKP_BASE>/dkp/logging/grafana` |

Full platform beat guide: `docs/NKP-CONSOLE-GUIDE.md`

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| Demo Wall shows `-` for all values | ArgoCD app not synced; check `kubectl -n argocd get app rx-demo` |
| Storefront unreachable | Check `kubectl -n istio-helm-gateway-ns get svc istio-helm-ingressgateway` — use port-forward fallback |
| Trace badge missing after checkout | `JAEGER_QUERY_URL` not set — trace ID is there, just not linked; copy manually |
| Canary weights stuck | Force ArgoCD sync: add `argocd.argoproj.io/refresh=hard` annotation |
| Policy card shows errors | Gatekeeper constraints not yet synced — wait 30 s and check `kubectl get constraints -A` |

Full troubleshooting: `docs/TROUBLESHOOTING.md`
Full reset procedure: `docs/RESET.md`
