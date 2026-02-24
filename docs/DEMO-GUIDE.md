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

## 3. Demo flow — 4-Act narrative

> **Audience tags**: `Both` = everyone, `Dev` = developer-focused, `Ops` = ops / platform team.
> Beats marked **(Optional)** can be skipped without breaking the flow.
> See [§3.5 Recommended run paths](#35-recommended-run-paths) for audience-specific timing.

---

### Act 1 — "The Platform" (~10 min)

*What NKP gives you before a single line of app code is written.*

| Beat | Title | Scenario | Audience | ~Time |
|------|-------|----------|----------|-------|
| 1 | Open Demo Wall, introduce the stack | `scenario/baseline` | Both | 3 min |
| 2 | Multi-cluster fleet (Kommander) | — | Ops | 2 min |
| 3 | Platform add-ons + quotas | — | Both | 2 min |
| 4 | Guardrails: RBAC + Policy (dryrun) | — | Ops | 3 min |

---

#### Beat 1 — Open the Demo Wall and introduce the stack

**Scenario**: `scenario/baseline` | **Audience**: Both | **~3 min**

**Action**: Open the Demo Wall. Set scenario to `scenario/baseline`.

**What the audience sees**:
- Scenario card: `scenario/baseline` — "Stable baseline — 100% traffic to v1"
- CD Status: `Synced / Healthy`
- Traffic: `v1 / v2 = 100 / 0`
- Policy: compliance %

**What you say**: _"Everything on screen is live — the Demo Wall pulls from
the Kubernetes API every five seconds. The only way to change the cluster
state is to change the Git branch. No kubectl apply, no live YAML edits.
That is GitOps."_

---

#### Beat 2 — Multi-cluster fleet (Kommander)

**Audience**: Ops | **~2 min**

**Action**: Open **Kommander → Clusters**.

**What to show**: The attached workload cluster, version, and health.

**What you say**: _"One Kommander manages every cluster in this environment.
Add a new cluster and it inherits the same policies and add-ons automatically."_

---

#### Beat 3 — Platform add-ons + quotas (Kommander)

**Audience**: Both | **~2 min**

**Action**: **Kommander → Applications** (workspace-scoped tab), then **Clusters → [workload cluster] → Namespaces → demo-app**.

**What to show**:
- Applications: Istio, Kiali, Jaeger, Grafana — all `Deployed`.
- Namespace view: live quota usage — pods, CPU request, memory.

Terminal side-by-side:
```bash
kubectl describe resourcequota demo-app-quota -n demo-app
```

**What you say**: _"The entire observability stack was deployed from NKP's app
catalog — one GitOps commit, no manual Helm installs. And every team namespace
has a hard quota baked in. A rogue deployment can't starve the cluster."_

---

#### Beat 4 — Guardrails: RBAC + Policy (dryrun)

**Audience**: Ops | **~3 min**

**Action**: **Kommander → Access Control → Roles**, then show Gatekeeper constraints.

**What to show**:
- RBAC roles: `dev-role-demo-app` (read-only) vs `ops-role-demo-app` (full).
- ArgoCD → `rx-demo` → Resources tab → filter `Constraint`.
- Demo Wall policy card: compliance %.

Terminal:
```bash
kubectl get roles -n demo-app -o wide
kubectl get constraints -A

# Live violation demo (non-blocking dryrun):
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
# Watch compliance card drop on Demo Wall
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

**What you say**: _"Developers can observe their workloads but cannot change
replicas — least-privilege is baked in. And Gatekeeper audits every object
continuously. We're in dryrun mode now — the bad pod ran, but it's flagged.
Later I'll show you what happens when we flip to enforce."_

> **Setup for Act 4**: The audience has now seen the violation pod run in dryrun mode.
> In Beat 16 you'll apply the same pod under `deny` — and it will be rejected at admission.

---

**Transition**: _"The platform is ready — quotas, RBAC, policy, observability, all from Git. Now let's ship an application update the GitOps way."_

---

### Act 2 — "Ship It" (~18 min)

*Progressive delivery from first canary to full cutover.*

| Beat | Title | Scenario | Audience | ~Time |
|------|-------|----------|----------|-------|
| 5 | Start the canary (10%) | `scenario/canary-10` | Both | 4 min |
| 6 | Service mesh topology (Kiali) | `scenario/canary-10` | Dev | 4 min |
| 7 | Distributed traces (Jaeger) | `scenario/canary-10` | Dev | 4 min |
| 8 | Ramp the canary (50% → 100%) | `canary-50` → `canary-100` | Both | 3 min |
| 9 | (Optional) Shadow testing — traffic mirroring | `scenario/mirror-v2` | Dev | 3 min |

---

#### Beat 5 — Start the canary (10%)

**Scenario**: `scenario/canary-10` | **Audience**: Both | **~4 min**

**Action**: Switch to `scenario/canary-10` in ArgoCD.

Watch the Demo Wall:
- Traffic card changes to `v1 / v2 = 90 / 10`
- CD Status briefly shows `Progressing`, then `Synced / Healthy`
- Intent shows: _"Progressive delivery — 10% traffic shifted to v2"_
- Next hint shows: `canary-50`

**Storefront**: Open two browser tabs. Refresh a few times — most loads show the
blue (v1) theme. Roughly 1 in 10 loads shows the green (v2) theme. Point out the
color difference to the audience.

**What you say**: _"I changed one line in Git — the branch pointer. ArgoCD
reconciled 12 Kubernetes resources in under 30 seconds. Ten percent of real
users are now seeing v2. No downtime, no kubectl apply."_

---

#### Beat 6 — Service mesh topology (Kiali)

**Scenario**: `scenario/canary-10` | **Audience**: Dev | **~4 min**

**Action**: Open **Kiali** (via Kommander SSO or Demo Wall platform link).

**What to show** (with `canary-10` active):
- Live traffic graph: frontend → payment-mock v1 and v2.
- Click the v2 edge: request rate, error rate, latency histogram.

**What you say**: _"Zero custom instrumentation. Istio captures every
request automatically. Kiali shows the topology and health of every
service-to-service call in real time."_

---

#### Beat 7 — Distributed traces (Jaeger)

**Scenario**: `scenario/canary-10` | **Audience**: Dev | **~4 min**

**Action**: In the storefront, click **Checkout**. Note the **Last Trace** badge
in the bag panel. If `JAEGER_QUERY_URL` is configured, click **→ Jaeger** to jump
directly. Otherwise copy the trace ID and paste into Jaeger search.

**What to show** in Jaeger:
- Service: `frontend` → Find Traces → open the checkout trace.
- The span waterfall: `frontend` → `checkout-api` → `payment-mock` (4 services, ~7 spans).
- Point out: each service added its own span. The trace crossed service boundaries automatically.

**What you say**: _"Every checkout generates a distributed trace across all four
services. This is how we'll prove v2 is healthy before ramping further — and
how we'll diagnose problems when things go wrong."_

---

#### Beat 8 — Ramp the canary (50% → 100%)

**Scenario**: `scenario/canary-50` → `scenario/canary-100` | **Audience**: Both | **~3 min**

**Action**: Switch to `scenario/canary-50`, then `scenario/canary-100`.

Watch:
- Demo Wall traffic card: 50/50 → 0/100
- Kiali graph updates live
- Storefront: all loads now show the green (v2) theme

**What you say**: _"Two more branch switches. Fifty-fifty, then full cutover.
Same workflow every time — Git is the control plane."_

---

#### Beat 9 — (Optional) Shadow testing with traffic mirroring

**Scenario**: `scenario/mirror-v2` | **Audience**: Dev | **~3 min**

> Best shown *before* the canary ramp (between Beats 7 and 8) if you want to tell
> the story chronologically: mirror first, then canary. Works in either position.

**Action**: Switch to `scenario/mirror-v2` in ArgoCD.

**What to show**:
- **Demo Wall**: Traffic card shows `v1 / v2 = 100 / 0 (mirror)` — users see only v1.
- **Kiali**: A dashed "mirror" edge appears from frontend to payment-mock-v2.
  v2 receives 100% shadow traffic but returns no responses to users.
- **Jaeger**: Search for service `payment-mock` — v2 traces appear alongside v1.
  v2 is processing real traffic shapes without any user impact.

**What you say**: _"Traffic mirroring sends a copy of every request to v2 in the
background. Users see only v1. We can validate v2 under real traffic patterns
with zero risk — before we even start the canary."_

Return to `scenario/canary-10` (or `scenario/baseline`) when done.

---

**Transition**: _"v2 is validated — traces look clean, canary metrics are green. But what happens when something goes wrong in production?"_

---

### Act 3 — "Break It, Find It, Fix It" (~18 min)

*Incident response — the observability payoff.*

| Beat | Title | Scenario | Audience | ~Time |
|------|-------|----------|----------|-------|
| 10 | Inject latency (the slow checkout) | `scenario/incident-latency` | Both | 3 min |
| 11 | Root cause in Jaeger | `scenario/incident-latency` | Dev | 5 min |
| 12 | (Optional) Inject errors (the broken checkout) | `scenario/incident-error` | Dev | 4 min |
| 13 | (Optional) Correlate: traces → logs | `scenario/incident-*` | Dev | 3 min |
| 14 | Rollback via GitOps | `scenario/baseline` | Both | 3 min |

---

#### Beat 10 — Inject latency (the slow checkout)

**Scenario**: `scenario/incident-latency` | **Audience**: Both | **~3 min**

**Action**: Switch to `scenario/incident-latency`.

Demo Wall shows:
- Traffic: 90/10 (re-split to canary)
- Intent: _"Incident drill — v2 injecting 1 s latency, watch Jaeger traces"_

**In the storefront**: Click **Checkout** three times. Watch the Activity box show
slower responses (~1 s per checkout). The **Last Trace** badge appears in the bag panel.

If `JAEGER_QUERY_URL` is configured: click **→ Jaeger** to jump directly to
the trace. Otherwise copy the trace ID and paste into Jaeger search.

**What you say**: _"Something is wrong. Checkouts that used to take 200 ms are
now taking over a second. Let's find out why."_

---

#### Beat 11 — Root cause in Jaeger

**Scenario**: `scenario/incident-latency` | **Audience**: Dev | **~5 min**

**Action**: Open **Jaeger** (via Demo Wall link or Kommander SSO).

- Service: `frontend` → Find Traces → open the trace from the slow checkout.
- Expand spans: `frontend` → `checkout-api` → `payment-mock-v2`.
- The `payment-mock-v2` span shows the 1 s delay — highlighted in the waterfall.

**What you say**: _"Three clicks: open the trace, expand the spans, find the
culprit. payment-mock v2 added a full second of latency. We pinpointed the
exact service and the exact call — without grepping a single log."_

---

#### Beat 12 — (Optional) Inject errors (the broken checkout)

**Scenario**: `scenario/incident-error` | **Audience**: Dev | **~4 min**

**Action**: Switch to `scenario/incident-error`.

Demo Wall shows:
- Intent: _"Incident drill — v2 returning errors"_
- Traffic: 90/10

**What to show**:
- **Storefront**: Click Checkout several times. Most succeed, but roughly 1 in 10
  returns a failure (5xx from payment-mock-v2).
- **Kiali**: Red error edges appear on the `payment-mock-v2` service. Error rate
  percentage is visible on the edge label.
- **Jaeger**: Filter traces by `error=true` — the failed spans show `payment-mock-v2`
  returning a 500 status.

**What you say**: _"Different failure mode, same diagnosis workflow. Latency was
subtle — errors are obvious in Kiali. Both lead you straight to the trace."_

---

#### Beat 13 — (Optional) Correlate: traces → logs

**Scenario**: `scenario/incident-latency` or `scenario/incident-error` | **Audience**: Dev | **~3 min**

> Use whichever incident scenario is still active.

**Action**: Copy a trace ID from the storefront's Last Trace badge (or from Jaeger).

Terminal — grep logs by trace ID:
```bash
# Replace <TRACE_ID> with the 32-char hex trace ID
kubectl -n demo-app logs -l app=payment-mock --tail=100 | grep "<TRACE_ID>"
```

The matching log line includes `trace_id` and `span_id` fields in the JSON output.

If Grafana Loki is available:
```
{namespace="demo-app"} |= "<TRACE_ID>"
```

**What you say**: _"Every log line carries the trace ID and span ID automatically —
OpenTelemetry injects them. One trace ID connects the Jaeger waterfall to the
exact log lines from every service that handled that request. No guessing which
request failed."_

---

#### Beat 14 — Rollback via GitOps

**Scenario**: `scenario/baseline` | **Audience**: Both | **~3 min**

**Action**: Switch back to `scenario/baseline` in ArgoCD.

- Traffic returns to 100/0
- Demo Wall shows Healthy
- Kiali graph normalises

Terminal — show the audit trail:
```bash
git log --oneline -5
```

**What you say**: _"Rollback is the same operation as the canary deploy — one
branch change in Git. ArgoCD reconciles in under 30 seconds. And look at the
git log — every change is an auditable commit. Who changed what, when, and why."_

---

**Transition**: _"That's the core workflow — ship, observe, diagnose, roll back.
Now let me show you platform capabilities that go deeper."_

---

### Act 4 — "Go Deeper" (pick 1–2 tracks, 6–8 min each)

*Choose based on audience. Each track is self-contained.*

---

#### Track A — Guardrails & Compliance (Ops / Security audience)

*Narrative: "In Act 1 we saw guardrails in audit mode. Now let's flip them to enforce."*

| Beat | Title | Scenario | ~Time |
|------|-------|----------|-------|
| 15 | Quota enforcement | `scenario/quota-pressure` | 3 min |
| 16 | Policy enforcement (deny mode) | `scenario/policy-enforce` | 3 min |

---

##### Beat 15 — Quota enforcement

**Scenario**: `scenario/quota-pressure` | **~3 min**

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

##### Beat 16 — Policy enforcement: Gatekeeper deny mode

**Scenario**: `scenario/policy-enforce` | **~3 min**

> **Callback to Act 1**: In Beat 4 the same violation pod ran successfully under dryrun.
> Now Gatekeeper is in deny mode — the pod will be rejected at admission.

**Action**: Switch to `scenario/policy-enforce` in ArgoCD.

What changes:
- `K8sDemoRequiredLabels` constraint flips from `dryrun` → `deny`
- Demo Wall policy card stays green (existing workloads are compliant)
- ArgoCD shows the constraint as `Synced / Healthy`

Now apply the same violation pod from Act 1:
```bash
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
```

The pod is **rejected at admission** — unlike Beat 4 (dryrun), this one never starts:
```
Error from server ([demo-required-labels] label 'version' is required): ...
```

Show the error message to the audience. Then confirm nothing was created:
```bash
kubectl -n demo-app get pods | grep policy-violation  # nothing
```

**What you say**: _"Same pod, same policy, different action. In Act 1 the pod
ran and was flagged. Now it's rejected before Kubernetes even schedules it.
One line in Git — `enforcementAction: deny` — is the difference between audit
and enforcement."_

Return to baseline when done.

---

#### Track B — Resilience & Autoscaling (Infra / Platform audience)

*Narrative: "The platform handles failures and scaling automatically."*

| Beat | Title | Scenario | ~Time |
|------|-------|----------|-------|
| 17 | Node failure resilience | `scenario/node-failure` | 4 min |
| 18 | KEDA autoscaling (scale to zero) | `scenario/keda-checkout` | 4 min |
| 18b | Node autoscaling (CAPI provisions new workers) | `scenario/node-autoscale` | 5 min |

---

##### Beat 17 — Node failure resilience

**Scenario**: `scenario/node-failure` | **~4 min**

> Demonstrates Kubernetes pod rescheduling and PodDisruptionBudgets when a worker node is removed.

**Action**: Switch to `scenario/node-failure` in ArgoCD.

What changes:
- All v1 services run **2 replicas** with pod anti-affinity (spread across nodes)
- PodDisruptionBudgets (`minAvailable: 1`) protect every service
- Demo Wall **Node Health** card shows node status; pod placement sub-rows appear under workloads

```bash
# Before the demo: verify pods are spread across nodes
kubectl -n demo-app get pods -o wide
```

Now simulate the failure — in **NKP Console → Clusters → [workload cluster] → Machines**, delete one worker node (or cordon it from the terminal):

```bash
# Option A: cordon + drain (non-destructive, reversible)
NODE=$(kubectl get nodes -l node-role.kubernetes.io/control-plane!= -o jsonpath='{.items[0].metadata.name}')
kubectl cordon "$NODE"
kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data

# Option B: delete via NKP console (CAPI will auto-replace the node)
```

Watch the Demo Wall:
- Node Health card flips one node to **NotReady**
- Pods on the drained node go `Pending`, then reschedule to surviving nodes
- PDBs ensure at least 1 replica stays `Running` throughout the disruption

```bash
# Watch rescheduling in real time
kubectl -n demo-app get pods -o wide -w
```

**What you say**: _"I just killed a worker node. Kubernetes noticed within seconds, evicted the pods,
and rescheduled them to healthy nodes — all while the PodDisruptionBudget ensured no service went to
zero replicas. The storefront stayed up the entire time."_

If using NKP CAPI: _"Meanwhile, NKP's Cluster API is already provisioning a replacement node. In a few
minutes the cluster will be back to full capacity — no ops ticket, no manual intervention."_

Uncordon when done (if using Option A):
```bash
kubectl uncordon "$NODE"
```

Return to baseline when done.

---

##### Beat 18 — KEDA autoscaling (scale to zero)

**Scenario**: `scenario/keda-checkout` | **~4 min**

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

##### Beat 18b — Node autoscaling (CAPI provisions new workers)

**Scenario**: `scenario/node-autoscale` | **~5 min**

> Demonstrates Cluster Autoscaler + CAPI provisioning new worker nodes in response to unschedulable pods.

**Pre-step (once per cluster setup — management cluster kubeconfig required):**

The cluster ships with `min=max=4` (pinned). NKP uses ClusterClass topology, so the autoscaler
annotations must be updated on the **Cluster** object — patching the MachineDeployment directly
is reverted by the topology controller within seconds.

```bash
# Run against the management cluster (auth/C01/nkp.conf)
kubectl --kubeconfig auth/C01/nkp.conf \
  -n kommander-default-workspace \
  patch cluster workload02 --type json \
  -p '[{"op":"replace","path":"/spec/topology/workers/machineDeployments/0/metadata/annotations/cluster.x-k8s.io~1cluster-api-autoscaler-node-group-max-size","value":"8"}]'

# Verify it propagated to the MachineDeployment (allow ~5 s for topology reconcile)
kubectl --kubeconfig auth/C01/nkp.conf \
  -n kommander-default-workspace \
  get machinedeployment workload02-md-0-p72kw \
  -o jsonpath='{.metadata.annotations.cluster\.x-k8s\.io/cluster-api-autoscaler-node-group-max-size}'
# Expected output: 8
```

**Action**: Switch to `scenario/node-autoscale` in ArgoCD.

What happens:
- ArgoCD creates the `demo-pressure` namespace and a 6-replica Deployment (`node-pressure`)
- Each pod requests `2 CPUs` + `4 Gi` memory — no current worker can fit even one of these (workers are at ~85% CPU)
- All 6 pods immediately enter **Pending** state
- Cluster Autoscaler detects unschedulable pods and requests 2 new worker nodes from CAPI
- New workers provision and join the cluster (~3–5 minutes on NKP)
- Pending pods are scheduled and flip to **Running**

Watch the Demo Wall:
- **Node Autoscaler** card appears (hidden on all other scenarios)
- Value shows `"N pods Pending — scaling up"` in amber while autoscaling
- Sub-line tracks worker count as new nodes join: `Workers: 4 / 6 Ready`
- Once all pods schedule: `"All 6 pods Running"` in green
- **Node Health** card shows the rising node count in real time

```bash
# Watch pending pods on the workload cluster
kubectl -n demo-pressure get pods -w

# Watch new nodes join
kubectl get nodes -w

# See autoscaler decision log (management cluster)
kubectl --kubeconfig auth/C01/nkp.conf \
  -n kube-system logs -l app=cluster-autoscaler --tail=50 -f
```

**What you say**: _"I applied 6 pods that couldn't fit on any existing worker. The Cluster Autoscaler noticed
the Pending state within 30 seconds and asked NKP's Cluster API to provision new worker nodes.
No manual intervention — the platform figured out what it needed and provisioned it. When I delete
the scenario, those nodes will scale back down automatically."_

Return to baseline when done (the `demo-pressure` namespace and pods are pruned automatically):
```bash
kubectl -n argocd patch application rx-demo --type merge \
  -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

> **Note**: Scale-down of the extra worker nodes may take 10–15 minutes after the pressure pods are
> removed (cluster autoscaler default scale-down delay). This is normal and can be highlighted as
> a cost-optimisation story: _"The cluster right-sizes itself — it won't keep idle nodes warm."_

---

### Closing

#### Beat 19 — End session

**Action**: Switch to `scenario/load-off`.

This stops the load generator. The cluster is idle and safe to leave.

> **Always end on `scenario/load-off`** — never leave load running after a demo session.

---

### 3.5. Recommended run paths

| Audience | ~Time | Beats | Focus |
|----------|-------|-------|-------|
| **Exec briefing** | 25 min | 1–6, 8, 10–11, 14, 19 | GitOps + incident story (skip deep observability) |
| **Developer team** | 45 min | 1–14, 19 | Full observability deep dive incl. traces, mirroring, log correlation |
| **Ops / Platform team** | 45 min | 1–6, 8, 10–11, 14–16, 19 | Core flow + guardrails & compliance (Track A) |
| **Infra / SRE team** | 50 min | 1–6, 8, 10–11, 14, 17–18b, 19 | Core flow + resilience & autoscaling (Track B) |
| **Full showcase** | 65 min | All beats (1–18b, 19) | Everything — both tracks |

---

## 4. Scenario reference

| Branch | What it does | Intent (shown in Demo Wall) | Used in | Logical next |
|---|---|---|---|---|
| `scenario/baseline` | Normal app, all v1, baseline load | Stable baseline — 100% traffic to v1 | Beats 1–4, 14 | `canary-10` |
| `scenario/load-off` | Normal app, load disabled | Load off — cluster at rest | Beat 19 | `baseline` |
| `scenario/load-peak` | Normal app, high load | Peak load — stress-testing v1 capacity | (ad-hoc) | `baseline` |
| `scenario/canary-10` | 90/10 split, baseline load | Progressive delivery — 10% to v2 | Beats 5–7 | `canary-50` |
| `scenario/canary-50` | 50/50 split, baseline load | Progressive delivery — 50/50 split | Beat 8 | `canary-100` |
| `scenario/canary-100` | 0/100 full cutover | Full cutover — 100% traffic on v2 | Beat 8 | `incident-latency` |
| `scenario/incident-latency` | v2 adds 1 s latency, 90/10 | Incident drill — v2 injecting latency | Beats 10–11, 13 | `incident-error` |
| `scenario/incident-error` | v2 returns 10% errors, 90/10 | Incident drill — v2 returning errors | Beat 12 | `baseline` |
| `scenario/mirror-v2` | Mirror all traffic to v2 silently | Traffic mirroring — shadow v2 | Beat 9 | `canary-10` |
| `scenario/keda-checkout` | KEDA scales checkout-api to zero | Autoscaling — scale to zero | Beat 18 | `baseline` |
| `scenario/quota-pressure` | 20 pause-pods fill ~75% pod quota | Quota pressure — guardrails active | Beat 15 | `baseline` |
| `scenario/policy-enforce` | Gatekeeper deny on required-labels | Policy enforcement — deny mode | Beat 16 | `baseline` |
| `scenario/node-failure` | 2-replica HA + PDBs, baseline load | Node resilience — evict & reschedule | Beat 17 | `baseline` |
| `scenario/node-autoscale` | 6 pressure pods (2 CPU each) exhaust workers | Node autoscaling — CAPI provisions new workers | Beat 18b | `baseline` |

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
