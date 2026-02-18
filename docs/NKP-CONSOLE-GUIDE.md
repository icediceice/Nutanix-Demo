# NKP Console Guide — Platform Demo Beats

This document maps each demo capability to the right UI surface and gives
exact navigation steps for the operator. The key design principle:

> **Show platform capabilities in the NKP console wherever the feature lives
> natively. Use the Demo Wall only for signals the platform UI does not surface
> (canary weights, scenario branch, live KPIs).**

---

## Surface Assignment Matrix

| Capability | Primary Surface | Reinforcement |
|---|---|---|
| Scenario branch / GitOps CD | **Demo Wall** → ArgoCD | `kubectl -n argocd get app rx-demo -o wide` |
| Canary traffic weights | **Demo Wall** + Kiali graph | VirtualService YAML |
| Loadgen profile | **Demo Wall** | `kubectl -n demo-ops get deploy demo-loadgen` |
| Resource Quotas | **Kommander Console** | `kubectl describe quota -n demo-app` |
| LimitRange (per-container) | **Kommander Console** | `kubectl describe limits -n demo-app` |
| RBAC / Access Control | **Kommander Console** | `kubectl get rolebindings -n demo-app -o wide` |
| Platform Add-ons / catalog | **Kommander Console** | `kubectl get appdeployments -A` |
| Policy compliance (Gatekeeper) | **Demo Wall** + **ArgoCD** | `kubectl get constraints -A` |
| Service mesh topology | **Kiali** (via Kommander SSO) | Demo Wall traffic card |
| Distributed traces | **Jaeger** (via Kommander SSO) | Storefront trace IDs |
| Metrics & dashboards | **Grafana** (via Kommander SSO) | Demo Wall KPI cards |
| Multi-cluster management | **Kommander Console** | — |

---

## Beat-by-Beat: NKP Console Navigation

Open the NKP platform URL from the Demo Wall **Platform Access** section (the
`Kommander` link). All paths below are relative to that base URL.

---

### Beat 1 — Platform Overview: Multi-Cluster View

**Where**: `/dkp/kommander/dashboard` → **Clusters**

**What to show**:
- The attached workload cluster, its version, and health status.
- NKP manages the full lifecycle — one pane across many clusters.

**Talking point**: _"One Kommander instance manages every cluster in this
environment. From here we can see cluster health, push add-ons, and enforce
policies — all without SSHing into a node."_

---

### Beat 2 — Resource Quotas

**Where**: `/dkp/kommander/dashboard` → **Clusters** → select the workload
cluster → **Namespaces** → filter/select `demo-app`

The namespace detail panel shows live ResourceQuota usage:
- `pods`: 40 max
- `requests.cpu`: 4 cores
- `requests.memory`: 4 Gi
- `limits.cpu`: 20 cores

Drill into `demo-ops` to show the ops namespace has a tighter budget (20 pods, 2 CPU req).

**Terminal reinforcement** (run side-by-side if projected):
```bash
kubectl describe resourcequota demo-app-quota -n demo-app
kubectl describe resourcequota demo-ops-quota -n demo-ops
kubectl describe limitrange default-limits -n demo-app
```

**Talking point**: _"Every team namespace has a hard quota. A rogue deployment
can't starve the rest of the cluster — the platform enforces guardrails
automatically via GitOps."_

---

### Beat 3 — RBAC / Access Control

**Where**: `/dkp/kommander/dashboard` → **Access Control** → **Roles**

**What to show**:
- `dev-role-demo-app` — read-only: list/get pods, deployments, services.
- `ops-role-demo-app` — read-write: full management of workloads.
- `ops-role-demo-ops` — ops namespace management (loadgen, demo-wall).

**Terminal reinforcement**:
```bash
kubectl get roles -n demo-app -o wide
kubectl get rolebindings -n demo-app -o wide
```

**Talking point**: _"Developers can observe their workloads but cannot change
replicas or edit Deployments. Operators get full access. No one has cluster-admin
by default — least-privilege baked in."_

---

### Beat 4 — Platform Add-ons (AppDeployments)

**Where**: `/dkp/kommander/dashboard` → **Applications** (workspace-scoped)

**What to show**:
- Istio, Kiali, Jaeger installed and `Deployed` / healthy.
- Each was enabled by a single `AppDeployment` manifest committed to Git — no
  manual Helm installs.

**Terminal reinforcement**:
```bash
# See what Kommander-managed apps are deployed
kubectl get appdeployments -A 2>/dev/null || \
  kubectl get helmreleases -n kommander-default-workspace -o wide
```

**Talking point**: _"The entire observability stack — Istio, Kiali, Jaeger,
Grafana — was deployed by NKP's app catalog with a single GitOps commit. Every
new cluster we onboard gets the same stack automatically."_

---

### Beat 5 — Policy Governance (Gatekeeper)

**Split across two surfaces** for maximum impact:

**Step A — ArgoCD** (GitOps source of truth):
ArgoCD UI → `rx-demo` app → **Resources** tab → filter by `Constraint`
- Show the three demo constraints synced and `Healthy`.
- This proves policy is code — it lives in Git, not in someone's head.

**Step B — Demo Wall** (live compliance):
The **Policy** card shows real-time compliance % and violation counts from the
running Gatekeeper constraints.

**Step C — Terminal** (enforcement evidence):
```bash
# Show all constraints and their violation counts
kubectl get constraints -A

# Show a specific constraint's violations
kubectl get k8sdemorequiredlabels.constraints.gatekeeper.sh \
  demo-required-labels -o jsonpath='{.status.totalViolations}{"\n"}'

# Apply a deliberate violating pod (non-blocking dryrun)
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
# Observe the Demo Wall compliance card drop
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

**Talking point**: _"Policy is just another Kubernetes resource. Gatekeeper
audits every object and surfaces violations here. We're in dryrun mode today —
flip `enforcementAction: deny` and the bad pod won't even schedule."_

---

### Beat 6 — Service Mesh Topology (Kiali)

**Where**: `<kommander-base>/dkp/kiali`
*(or port-forward: `kubectl -n kommander-default-workspace port-forward svc/kiali 20001:20001`)*

**What to show** (while `scenario/canary-10` or `canary-50` is active):
- The live traffic graph with v1/v2 split visible.
- Click the `frontend` → `payment-mock` edge: shows request rate, error rate,
  latency histogram.
- If `scenario/incident-latency` is active: the edge turns yellow/red.

**Talking point**: _"Zero custom instrumentation. Istio captures every request
automatically. Kiali shows the topology and health of every service-to-service
call in real time."_

---

### Beat 7 — Distributed Traces (Jaeger)

**Where**: `<kommander-base>/dkp/jaeger`

**What to show**:
- Service: `frontend` → Search → pick a recent trace.
- Expand spans: frontend → catalog-api → payment-mock (v1 or v2).
- During `scenario/incident-latency`: the payment-mock v2 span is highlighted red.

**Deep-link format** (construct in browser):
`<jaeger-base>/search?service=frontend&limit=20`

**Talking point**: _"Every click in the storefront generates a real distributed
trace. We can pinpoint exactly which service introduced that 500ms spike —
without grepping logs."_

---

### Beat 8 — Metrics & Dashboards (Grafana)

**Where**: `<kommander-base>/dkp/logging/grafana`

**Suggested dashboards**:
| Dashboard | Path in Grafana |
|---|---|
| Istio Service Dashboard | `d/istio-service` |
| Kubernetes / Namespaces | `d/k8s-namespaces` |
| Kubernetes / Workloads | `d/k8s-workloads` |

**What to show** during a canary scenario:
- Istio Service dashboard filtered to `payment-mock` — watch request rate split
  between v1 and v2.
- During `incident-latency`: the p99 latency panel spikes for v2.

**Talking point**: _"Metrics flow automatically from Istio into Prometheus and
into Grafana. No manual scrape configs — the mesh does it."_

---

## Quick Reference: Deep Links

Replace `<NKP_BASE>` with the URL shown in the Demo Wall **Platform Access →
Kommander** card.

| Destination | URL |
|---|---|
| Kommander Dashboard | `<NKP_BASE>/dkp/kommander/dashboard` |
| Clusters | `<NKP_BASE>/dkp/kommander/dashboard/clusters` |
| Applications catalog | `<NKP_BASE>/dkp/kommander/dashboard/applications` |
| Access Control | `<NKP_BASE>/dkp/kommander/dashboard/access-control` |
| Kiali | `<NKP_BASE>/dkp/kiali` |
| Jaeger | `<NKP_BASE>/dkp/jaeger` |
| Grafana | `<NKP_BASE>/dkp/logging/grafana` |
| ArgoCD | Separate LoadBalancer — see Demo Wall **Platform Access → ArgoCD** card |

---

## Demo Flow Recommendation

| Order | Beat | Surface |
|---|---|---|
| 1 | Bootstrap — point to Demo Wall, set scenario/baseline | Demo Wall |
| 2 | Multi-cluster overview | Kommander → Clusters |
| 3 | Add-ons catalog (Istio/Kiali/Jaeger deployed) | Kommander → Applications |
| 4 | Resource quotas live usage | Kommander → Namespaces |
| 5 | RBAC — dev vs ops roles | Kommander → Access Control |
| 6 | Switch to `scenario/canary-10` | Demo Wall → ArgoCD |
| 7 | Service mesh topology | Kiali |
| 8 | Policy governance | ArgoCD + Demo Wall |
| 9 | Escalate to `scenario/incident-latency` | Demo Wall |
| 10 | Trace the incident | Jaeger |
| 11 | Metrics spike | Grafana |
| 12 | Rollback — set `scenario/baseline` | Demo Wall → ArgoCD |
| 13 | End — set `scenario/load-off` | Demo Wall |
