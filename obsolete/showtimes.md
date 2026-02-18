# Showtime (Partner Demo Walkthrough)

This is the presenter script: what to open, what to say, what to click/run, and which `scenario/*` branch to switch to.

## 0) Preflight (2 minutes)

Set your kubeconfig (example):

```bash
export KUBECONFIG=auth/workload02-kubeconfig.conf
kubectl config current-context
kubectl get nodes
```

If the cluster is brand new, bootstrap once:

```bash
./scripts/bootstrap-demo.sh --branch scenario/load-off
```

Print all access points:

```bash
./scripts/print-access.sh
```

Expected before you start talking:
- ArgoCD `Application/rx-demo` is `Synced` and `Healthy`.
- Demo app URL responds.
- Demo Wall URL responds.

## 1) Open The Tabs (1 minute)

Open these in separate browser tabs:
- Kommander UI (cluster view, apps/add-ons, observability)
- ArgoCD UI (`rx-demo` Application page)
- Demo app (frontend URL)
- Demo Wall (demo-wall URL)
- Kiali (via Kommander UI plugin, or port-forward if needed)
- Jaeger (via Kommander UI plugin, or port-forward if needed)

If you need the ArgoCD password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d && echo
```

## 2) Story Setup (what you say)

1. Git is the control plane for the demo: we change a Git branch, not live YAML.
2. ArgoCD reconciles the cluster to match the branch (health and drift are visible).
3. The app runs v1 and v2 side-by-side; Istio controls how much traffic goes to v2.
4. Observability is first-class: service graph (Kiali) and traces (Jaeger).
5. Governance guardrails exist (Gatekeeper) but are non-blocking for the demo.

## 3) Start In A Safe State: `scenario/load-off` (1 minute)

Confirm you are on `scenario/load-off` (low/no traffic, canary weight 0%):

```bash
kubectl -n argocd get application rx-demo -o jsonpath='{.spec.source.targetRevision}{"\n"}'
```

If you need to force it:

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/load-off"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
kubectl -n argocd get application rx-demo -o wide
```

Show:
- ArgoCD says `Synced/Healthy`.
- Demo Wall reflects the branch and shows loadgen is off.

## 4) Turn On Baseline Traffic: `scenario/baseline` (2 minutes)

Switch to baseline traffic:

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

What to show while it reconciles:
- In ArgoCD: resources update, app stays healthy.
- In Demo Wall: loadgen becomes active, KPIs refresh.
- In Kiali: open the service graph for namespace `demo-app` and show traffic flowing.

Useful “what’s running” commands:

```bash
kubectl -n demo-ops get deploy,pod -o wide
kubectl -n demo-app get pod -o wide
```

## 5) Progressive Delivery (Canary) (5 minutes)

Move through canary branches and narrate “measured rollout”:

### 5.1 Canary 10%
```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/canary-10"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Show in Kiali:
- `frontend` traffic splitting between `v1` and `v2` (small % to v2).

### 5.2 Canary 50%
```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/canary-50"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Show:
- Kiali service graph clearly shows the split.
- Demo Wall shows updated canary weight.

### 5.3 (Optional) Canary 100%
```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/canary-100"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

## 6) Incident Drill (Latency or Error) (5 minutes)

Pick one depending on time:

### 6.1 Latency incident
This makes `payment-mock-v2` slow (branch-driven overlay).

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/incident-latency"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Show:
- Demo app feels slower (checkout path).
- Demo Wall KPIs reflect degraded behavior.
- Kiali: increased latency on the `payment-mock` leg.
- Jaeger: traces show long spans in `payment-mock` (filter by service and recent traces).

### 6.2 Error incident
This makes `payment-mock-v2` return errors at a rate (branch-driven overlay).

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/incident-error"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Show:
- Kiali: elevated error rate on the `payment-mock` leg.
- Jaeger: traces showing error spans.

### 6.3 Roll back live (the point of the demo)
Roll back by switching the branch:

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/baseline"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Narration:
- “Rollback is a Git change. ArgoCD converges back. We restore service fast.”

## 7) Peak Load (optional) (2 minutes)

If you want a “scale/pressure” moment:

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/load-peak"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

Show:
- Demo Wall loadgen state.
- Kiali traffic volume changes.

## 8) Governance (2 minutes)

Show that guardrails exist without blocking the session:

```bash
kubectl get constrainttemplates.templates.gatekeeper.sh
kubectl get constraints -A | rg demo- || true
```

Point to Demo Wall policy summary.

Optional (make it tangible with a non-blocking violation):

```bash
kubectl apply -f platform/policy/examples/policy-violation-example.yaml
kubectl -n demo-app get pod policy-violation-example -o wide
```

Then show the violation counters (may take 30-90s to update depending on Gatekeeper audit interval):

```bash
kubectl get k8sdemorequiredlabels.constraints.gatekeeper.sh demo-required-labels -o jsonpath='{.status.totalViolations}{"\n"}' || true
kubectl get k8sdemorequiredresources.constraints.gatekeeper.sh demo-required-resources -o jsonpath='{.status.totalViolations}{"\n"}' || true
kubectl get k8sdemonolatest.constraints.gatekeeper.sh demo-no-latest -o jsonpath='{.status.totalViolations}{"\n"}' || true
```

Cleanup:

```bash
kubectl -n demo-app delete pod policy-violation-example --ignore-not-found
```

## 9) End Session Safely (30 seconds)

Always end on low/no load:

```bash
kubectl -n argocd patch application rx-demo --type merge -p '{"spec":{"source":{"targetRevision":"scenario/load-off"}}}'
kubectl -n argocd annotate application rx-demo argocd.argoproj.io/refresh=hard --overwrite
```

## 10) Presenter Tips (practical)

Use these while presenting so you always have “proof”:

```bash
kubectl -n argocd get application rx-demo -o wide
kubectl -n demo-app get pod -o wide
kubectl -n demo-ops get deploy,pod -o wide
```

If a sync is stuck, first check the reason (usually a workload issue):

```bash
kubectl -n argocd describe application rx-demo | rg -n \"Failed|exceeded|forbidden|quota|ImagePull|error\" -n || true
kubectl -n demo-app get events --sort-by=.lastTimestamp | tail -n 30
```
