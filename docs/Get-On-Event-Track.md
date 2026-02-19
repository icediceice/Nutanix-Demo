# Get On Event Track — NKP GitOps Platform Demo (2 hours)

A complete presentation plan for the **Get On distributor partner event**.
Audience: partners (resellers, system integrators, managed service providers)
evaluating or onboarding with Nutanix NKP.

> **This document is the single reference for the presenter.**
> Technical demo beats reference `docs/DEMO-GUIDE.md` — keep both open.

---

## Table of Contents

1. [Event Overview](#1-event-overview)
2. [Audience Profile & Key Messages](#2-audience-profile--key-messages)
3. [Pre-Event Checklist](#3-pre-event-checklist)
4. [2-Hour Timeline](#4-2-hour-timeline)
5. [Segment Details](#5-segment-details)
6. [Presentation Materials](#6-presentation-materials)
7. [Post-Event Follow-Up](#7-post-event-follow-up)

---

## 1. Event Overview

| Item | Detail |
|------|--------|
| **Event** | Get On Partner Enablement — NKP Platform Demo |
| **Duration** | 2 hours (120 min) |
| **Format** | Live platform demo with interactive discussion |
| **Goal** | Show partners why NKP wins deals — and give them the confidence to position it |
| **Outcome** | Partners leave with: (1) a mental model of NKP's value, (2) demo stories they can retell to customers, (3) clear next steps |

### What this is NOT

- Not a sales pitch deck marathon — this is live platform proof
- Not a deep Kubernetes training — partners need the "what" and "why", not the "how to build from scratch"
- Not a feature checklist walkthrough — every segment tells a customer story

---

## 2. Audience Profile & Key Messages

### Who is in the room

| Role | What they care about | How to engage them |
|------|---------------------|--------------------|
| **Partner sales** | Deal size, competitive positioning, customer pain points | Business outcomes, TCO story, "what to say in the meeting" |
| **Partner pre-sales / SE** | Technical differentiation, demo repeatability, proof points | Live platform evidence, architecture clarity, hands-on moments |
| **Partner leadership** | Market opportunity, Nutanix partnership value, services revenue | Platform breadth, managed services angle, customer retention |
| **Technical consultants / SI** | Implementation complexity, Day 2 operations, integration | Automation depth, GitOps simplicity, observability stack |

### Five key messages (weave throughout)

| # | Message | When to land it |
|---|---------|-----------------|
| 1 | **"Everything is Git — one control plane for the entire platform."** | Act 1 (GitOps intro) |
| 2 | **"Ship safely — canary, mirror, roll back in seconds, not hours."** | Act 2 (progressive delivery) |
| 3 | **"Find the problem in 3 clicks, not 3 hours."** | Act 3 (incident drill) |
| 4 | **"Guardrails are built in — compliance without slowing teams down."** | Act 1 + Act 4 (policy) |
| 5 | **"One platform, Day 0 to Day 2 — deploy, observe, enforce, scale."** | Closing |

### Competitive positioning (know, don't lead with)

| Competitor | NKP advantage to highlight |
|------------|---------------------------|
| VMware Tanzu | NKP = full stack (compute + K8s + mesh + observability) from one vendor. No "bring your own monitoring." |
| Red Hat OpenShift | NKP runs on any infrastructure (Nutanix, AWS, Azure, bare metal). Simpler licensing. GitOps-native from Day 1. |
| Rancher / SUSE | NKP includes enterprise observability (Istio, Jaeger, Grafana) out of the box. Kommander multi-cluster management is built in, not bolted on. |
| DIY Kubernetes | NKP eliminates the "Kubernetes tax" — no team needed to maintain the platform. Partners sell managed services on top. |

> **Rule**: Never badmouth competitors by name during the demo. Position NKP on its own strengths. Use competitor knowledge only when a partner asks directly.

---

## 3. Pre-Event Checklist

### One week before

- [ ] Confirm cluster is running: `kubectl get nodes` — all nodes `Ready`
- [ ] Run bootstrap if needed: `./scripts/bootstrap-demo.sh --kubeconfig auth/workload02.conf --branch scenario/load-off`
- [ ] Verify all URLs work: `./scripts/print-access.sh --kubeconfig auth/workload02.conf`
- [ ] Test every scenario branch used in the demo (see §4 timeline):
  - `scenario/baseline`, `canary-10`, `canary-50`, `canary-100`
  - `scenario/mirror-v2`, `scenario/incident-latency`, `scenario/incident-error`
  - `scenario/quota-pressure`, `scenario/policy-enforce`
  - `scenario/load-peak`, `scenario/load-off`
- [ ] Verify Jaeger has traces: open Jaeger → service `frontend` → Find Traces
- [ ] Verify Kiali shows traffic graph: open Kiali → Graph → namespace `demo-app`
- [ ] Prepare slide deck (see [§6 Presentation Materials](#6-presentation-materials))
- [ ] Test screen sharing / projector setup — Demo Wall + terminal + NKP console must all be visible
- [ ] Print or share the Quick Reference card (see §6)

### Day of — 30 minutes before

- [ ] Set scenario to `scenario/baseline` and verify Demo Wall shows `Synced / Healthy`
- [ ] Open all browser tabs (pre-logged in):
  - Tab 1: Demo Wall (`http://<DEMO_WALL_LB>/`)
  - Tab 2: Storefront (`http://<ISTIO_INGRESS>/`)
  - Tab 3: ArgoCD (`https://<ARGOCD_LB>/`)
  - Tab 4: Kommander Dashboard (`https://<NKP_BASE>/dkp/kommander/dashboard`)
  - Tab 5: Kiali (`https://<NKP_BASE>/dkp/kiali`)
  - Tab 6: Jaeger (`https://<NKP_BASE>/dkp/jaeger`)
  - Tab 7: Grafana (`https://<NKP_BASE>/dkp/logging/grafana`)
- [ ] Open terminal with `kubectl` configured
- [ ] Open this document + `docs/DEMO-GUIDE.md` on your second screen
- [ ] Verify internet connectivity (SSO login, NKP console)
- [ ] Test audio / microphone

---

## 4. 2-Hour Timeline

| Time | Segment | Duration | Type | Scenario |
|------|---------|----------|------|----------|
| 0:00 | **Opening — Why NKP, Why Now** | 10 min | Talk + slides | — |
| 0:10 | **Act 1 — The Platform** | 15 min | Live demo | `baseline` |
| 0:25 | **Discussion: Platform value** | 5 min | Q&A | — |
| 0:30 | **Act 2 — Ship It (Progressive Delivery)** | 25 min | Live demo | `canary-*`, `mirror-v2` |
| 0:55 | **Discussion: Delivery & observability** | 5 min | Q&A | — |
| 1:00 | **Break** | 5 min | — | — |
| 1:05 | **Act 3 — Break It, Find It, Fix It** | 25 min | Live demo | `incident-*` |
| 1:30 | **Discussion: Incident response value** | 5 min | Q&A | — |
| 1:35 | **Act 4 — Go Deeper (Guardrails)** | 10 min | Live demo | `quota-pressure`, `policy-enforce` |
| 1:45 | **Partner Opportunity & Next Steps** | 10 min | Talk + discussion | — |
| 1:55 | **Closing + End Session** | 5 min | Wrap-up | `load-off` |
| **2:00** | **End** | | | |

---

## 5. Segment Details

---

### Segment 1 — Opening: Why NKP, Why Now (0:00 – 0:10)

**Format**: Slides + presenter talk (no demo yet)

**Purpose**: Set context before touching the keyboard. Partners need to know *why this matters to their customers* before seeing *how it works*.

**Talking points**:

1. **The customer problem**:
   _"Your customers are running Kubernetes — or they're about to. But Kubernetes alone is not a platform. They need observability, security, policy, multi-cluster management, and a delivery pipeline. Building that from scratch takes 6-12 months and a dedicated platform team."_

2. **What NKP solves**:
   _"NKP is the complete platform. Compute, Kubernetes, service mesh, observability, policy — one vendor, one support contract, one upgrade path. Your customer gets Day 2 operations on Day 0."_

3. **Why partners win**:
   _"Every NKP deployment is a services opportunity. Assessment, implementation, managed services, training. The platform creates long-term customer relationships, not one-time box sales."_

4. **What you're about to see**:
   _"I'm going to show you a live NKP environment running a real application. Everything you see is controlled by Git — I won't type a single kubectl apply. We'll ship a canary update, break something on purpose, find the root cause in three clicks, and roll back in seconds. This is the story you'll tell your customers."_

**Slides to prepare** (see §6):
- Slide 1: NKP platform stack diagram (compute → K8s → mesh → observability → policy)
- Slide 2: Customer pain points → NKP solution mapping
- Slide 3: Partner opportunity (services revenue, managed services, customer lifecycle)

---

### Segment 2 — Act 1: The Platform (0:10 – 0:25)

**Format**: Live demo — follow DEMO-GUIDE.md Beats 1–4

| Beat | What to show | Partner-focused talking point |
|------|-------------|------------------------------|
| 1 — Demo Wall | Demo Wall live, `scenario/baseline` | _"This dashboard pulls live data from the cluster every 5 seconds. Everything your customer's ops team needs on one screen — no Datadog license, no Splunk contract."_ |
| 2 — Multi-cluster (Kommander) | Kommander → Clusters | _"One console for every cluster. Your customer has 3 clusters today, 30 next year. Kommander scales with them — and every new cluster gets the same policies and tooling automatically."_ |
| 3 — Add-ons + Quotas | Kommander → Applications, then Namespaces | _"Istio, Kiali, Jaeger, Grafana — deployed with one click from the NKP catalog. No Helm expertise needed. And every namespace has resource quotas — the platform prevents noisy neighbors automatically."_ |
| 4 — RBAC + Policy (dryrun) | Kommander → Access Control, then policy violation demo | _"RBAC and OPA Gatekeeper policies are defined in Git. Developers get self-service access; security teams get audit compliance. Show your customer's CISO this screen."_ |

**Key moment**: When you apply the violation pod in Beat 4 and it runs (dryrun mode), tell the audience: _"Remember this — the pod ran. Later I'll flip one switch and it won't."_

**Transition to Q&A**: _"That's the platform before a single line of app code. Questions about what you just saw?"_

---

### Segment 3 — Discussion: Platform Value (0:25 – 0:30)

**Prompt questions for partners**:
- _"Which of your customers is struggling with Kubernetes platform management today?"_
- _"How are they handling observability — built in-house or third-party tools?"_
- _"Does their security team have visibility into what's running in the cluster?"_

**If the room is quiet**: Share a customer scenario:
_"A mid-size financial services company had 5 teams sharing 3 clusters. No quotas, no RBAC, no policy. One team's memory leak brought down production for everyone. NKP would have prevented that with the quotas and policies you just saw."_

---

### Segment 4 — Act 2: Ship It (0:30 – 0:55)

**Format**: Live demo — follow DEMO-GUIDE.md Beats 5–9 (all beats, including optional)

| Beat | What to show | Partner-focused talking point |
|------|-------------|------------------------------|
| 5 — Canary 10% | Switch to `canary-10`, show storefront v1 (blue) vs v2 (green) | _"One Git branch change. 10% of users see the new version. If something breaks, 90% of users never noticed. This is how your customers ship without fear."_ |
| 6 — Kiali topology | Kiali traffic graph showing v1/v2 split | _"The service mesh captures every request. Your customer sees exactly which service talks to which — no agents to install, no code to change."_ |
| 7 — Jaeger traces | Click Checkout → follow trace to Jaeger | _"Every user click generates a distributed trace across all services. This is the evidence that v2 is healthy — before ramping further. Show this to your customer's dev lead."_ |
| 8 — Ramp to 100% | `canary-50` → `canary-100`, storefront all green | _"Two more Git changes. Fifty-fifty, then full cutover. Same workflow every time. Your customer's release process becomes repeatable and auditable."_ |
| 9 — Traffic mirroring | Switch to `mirror-v2`, show Kiali dashed edge | _"Shadow testing. 100% of traffic is copied to v2 in the background. Users see only v1. Your customer validates the new version under real traffic with zero risk. Try doing this without a service mesh."_ |

**Key moment**: Beat 9 (mirroring) is the "wow" for technical partners. The dashed edge in Kiali makes it visual. Linger here.

**Transition to Q&A**: _"That's progressive delivery — canary, mirror, full cutover — all from Git. Questions before we break something?"_

---

### Segment 5 — Discussion: Delivery & Observability (0:55 – 1:00)

**Prompt questions**:
- _"How do your customers deploy today? kubectl apply? Helm? Jenkins pipeline?"_
- _"What happens when a bad deployment goes out — how long does rollback take?"_
- _"Do they have distributed tracing? How do they debug cross-service issues?"_

**Partner selling point to land**:
_"The implementation engagement for GitOps + progressive delivery + observability is 2-4 weeks of services. That's a repeatable services offering for every NKP customer."_

---

### Segment 6 — Break (1:00 – 1:05)

Five-minute break. Leave the Demo Wall visible on screen — it auto-refreshes and keeps the room engaged.

---

### Segment 7 — Act 3: Break It, Find It, Fix It (1:05 – 1:30)

**Format**: Live demo — follow DEMO-GUIDE.md Beats 10–14 (all beats)

This is the emotional peak of the demo. You're going to break the application, diagnose it live, and fix it — the audience experiences the "aha" moment.

| Beat | What to show | Partner-focused talking point |
|------|-------------|------------------------------|
| 10 — Inject latency | Switch to `incident-latency`, click Checkout 3x | _"Something is wrong. Checkouts are slow. Your customer's users are complaining. How long does it take your customer to find the problem today? Hours? Days?"_ |
| 11 — Root cause in Jaeger | Open trace, expand spans, find 1s delay in payment-mock-v2 | _"Three clicks. Open the trace, expand the spans, find the culprit. payment-mock v2 added a full second of latency. That took us 30 seconds. Without this? Your customer is grepping logs across 4 services."_ |
| 12 — Inject errors | Switch to `incident-error`, show Kiali red edges | _"Different failure mode. 10% of checkouts return errors. Kiali lights up red immediately. Same diagnosis workflow — Kiali for the overview, Jaeger for the detail."_ |
| 13 — Trace → log correlation | Copy trace ID, grep in kubectl logs | _"One trace ID connects the Jaeger waterfall to the exact log lines. No guessing which request failed. OpenTelemetry injects the correlation automatically."_ |
| 14 — Rollback | Switch to `baseline`, show `git log` | _"Rollback is a Git branch change. Under 30 seconds. And look at the git log — every change is an auditable commit. Who changed what, when, why. Your customer's auditor loves this."_ |

**Key moment**: The transition from Beat 10 (broken) to Beat 14 (fixed) should feel dramatic. Pause after the rollback. Let the Demo Wall refresh and show `Healthy`. Then say: _"That entire incident — detection, diagnosis, remediation — took under 5 minutes. No war room. No all-hands Slack thread."_

**Transition to Q&A**: _"That's the observability payoff. The platform paid for itself the first time it prevented a 3 AM incident call."_

---

### Segment 8 — Discussion: Incident Response Value (1:30 – 1:35)

**Prompt questions**:
- _"How do your customers handle production incidents today?"_
- _"What's their mean time to recovery? Hours? Days?"_
- _"Who gets the 3 AM phone call when something breaks?"_

**Partner selling points**:
- _"NKP with observability reduces MTTR from hours to minutes. That's the ROI story."_
- _"Every incident you just saw was diagnosed without SSH, without log aggregation setup, without custom dashboards. It's built in."_
- _"Managed services opportunity: partners who run NKP for their customers can offer SLA-backed incident response using these same tools."_

---

### Segment 9 — Act 4: Go Deeper — Guardrails (1:35 – 1:45)

**Format**: Live demo — follow DEMO-GUIDE.md Beats 15–16 (Track A: Guardrails & Compliance)

> For a partner audience, Track A (guardrails) is more compelling than Track B (resilience) because it speaks directly to the compliance and governance story that CISOs care about.

| Beat | What to show | Partner-focused talking point |
|------|-------------|------------------------------|
| 15 — Quota enforcement | Switch to `quota-pressure`, try to exceed quota | _"The platform hard-stopped the scale request. No human in the loop. Your customer's finance team sets the budget, the platform enforces it. Self-service for developers, guardrails for ops."_ |
| 16 — Policy enforcement | Switch to `policy-enforce`, apply same violation pod from Act 1 | _"Remember in Act 1, this pod ran? Now it's rejected at admission. One line changed in Git. This is the story for your customer's CISO — audit mode for testing, enforce mode for production. Same policy, different action."_ |

**Key moment**: The callback to Act 1 is powerful. The audience remembers the pod running earlier. Now it's blocked. The narrative arc lands.

---

### Segment 10 — Partner Opportunity & Next Steps (1:45 – 1:55)

**Format**: Slides + open discussion

**Talking points**:

1. **The services opportunity**:
   _"Every feature you saw today is a services engagement. Assessment: 'Is the customer ready for NKP?' Implementation: 2-4 weeks for GitOps + observability + policy. Managed services: ongoing platform operations. Training: teach the customer's team to use what we just showed."_

2. **Customer conversation starters**:
   - _"How are you managing Kubernetes across teams today?"_
   - _"What happens when a deployment goes wrong — how long does rollback take?"_
   - _"Does your security team have visibility into what's running in your clusters?"_
   - _"Are you paying for third-party observability on top of your Kubernetes platform?"_

3. **NKP deal components**:

   | Component | What it includes |
   |-----------|-----------------|
   | **NKP Platform** | Kubernetes + Kommander multi-cluster management |
   | **Service mesh** | Istio (included) — traffic management, mTLS, observability |
   | **Observability** | Jaeger, Kiali, Grafana, Prometheus (included) |
   | **Policy engine** | OPA Gatekeeper (included) |
   | **GitOps** | ArgoCD (included) |
   | **Partner services** | Assessment → Implementation → Managed → Training |

4. **Next steps for partners**:
   - Schedule a customer-facing demo (this same demo, 45-min exec version)
   - Request a lab environment for partner SE enablement
   - Access partner portal for NKP sales materials and pricing
   - Join the partner Slack channel for technical support

**Slides to prepare**:
- Slide 4: Services engagement model (assess → implement → manage → train)
- Slide 5: Customer conversation starters
- Slide 6: Next steps and partner resources

---

### Segment 11 — Closing (1:55 – 2:00)

**Action**: Switch to `scenario/load-off` (Beat 19).

**Closing statement**:
_"You saw one platform do everything — deploy, canary, observe, diagnose, roll back, enforce policy — all from Git. No third-party tools, no manual kubectl, no tribal knowledge. This is what your customers get with NKP. And this is the story you tell in every meeting."_

**Leave up on screen**: Demo Wall showing `scenario/load-off` — the clean, professional closing image.

**Share with attendees**: Quick Reference card (see §6) with demo URLs and key commands.

---

## 6. Presentation Materials

### Slides to prepare

Keep slides minimal. The live demo is the star — slides are only for framing.

| Slide | Content | When |
|-------|---------|------|
| 1 | **NKP Platform Stack** — diagram: Nutanix HCI → NKP Kubernetes → Service Mesh → Observability → Policy → GitOps | Opening |
| 2 | **Customer Pain Points** — "Kubernetes is not a platform" + 4 pain points mapped to NKP solutions | Opening |
| 3 | **Partner Opportunity** — services revenue model, customer lifecycle | Opening |
| 4 | **Services Engagement Model** — assess → implement → manage → train | Closing |
| 5 | **Customer Conversation Starters** — 4 questions to open customer meetings | Closing |
| 6 | **Next Steps** — lab access, partner portal, Slack channel, demo scheduling | Closing |

### Quick Reference Card (handout or digital share)

Prepare a one-page handout or PDF for partners to take away:

```
NKP GitOps Demo — Quick Reference
──────────────────────────────────
Platform capabilities shown:
  - GitOps (ArgoCD) — all changes via Git, audit trail built in
  - Progressive delivery — canary 10% → 50% → 100%, traffic mirroring
  - Service mesh (Istio) — automatic traffic capture, mTLS, topology
  - Distributed tracing (Jaeger) — 3-click root cause analysis
  - Metrics & dashboards (Grafana) — built-in, no setup
  - Policy engine (Gatekeeper) — audit mode → enforce mode, from Git
  - Resource quotas — hard limits per namespace, automatic enforcement
  - RBAC — least-privilege by default, managed in Kommander
  - Multi-cluster management (Kommander) — one console for all clusters

Key demo stories to retell:
  1. "One Git change ships a canary to 10% of users in 30 seconds"
  2. "Three clicks to find the root cause of a production incident"
  3. "Rollback is a Git revert — under 30 seconds, fully auditable"
  4. "Same policy, one line changed — audit mode to enforce mode"

Customer conversation starters:
  - "How are you managing Kubernetes across teams today?"
  - "What happens when a deployment goes wrong?"
  - "Does your security team have cluster visibility?"
  - "Are you paying extra for observability?"
```

### Demo environment access (for partner SEs)

If partners want to replay the demo in their own sessions, provide:
- Access to a lab environment (NKP cluster + this repo)
- `docs/DEMO-GUIDE.md` — the complete operator guide
- `docs/PREREQS.md` — what to install
- `scripts/bootstrap-demo.sh` — one-command setup
- Recommended: 45-min "Exec briefing" run path (DEMO-GUIDE.md §3.5)

---

## 7. Post-Event Follow-Up

### Within 24 hours

- [ ] Send thank-you email with:
  - Quick Reference card (PDF)
  - Link to NKP partner portal
  - Link to lab environment request form
  - Recording of the session (if recorded)
- [ ] Share this repo (or a sanitized version) with technical partners who want to run the demo themselves

### Within 1 week

- [ ] Follow up with partners who expressed interest in customer demos
- [ ] Schedule partner SE enablement sessions (hands-on lab)
- [ ] Connect interested partners with Nutanix channel team for deal registration

### Metrics to track

| Metric | Target |
|--------|--------|
| Partner demos scheduled within 2 weeks | 3+ |
| Customer-facing demos booked within 1 month | 5+ |
| Lab environment requests | 50% of attendees |
| Partner SE enablement sessions scheduled | 2+ |

---

## Appendix: Scenario Branches Used in This Track

All branches are pre-built and tested. No configuration changes needed during the demo.

| Branch | Used in | Purpose |
|--------|---------|---------|
| `scenario/baseline` | Opening, Act 1, Rollback | Stable starting point |
| `scenario/canary-10` | Act 2 | 10% canary — progressive delivery start |
| `scenario/canary-50` | Act 2 | 50/50 split — midpoint |
| `scenario/canary-100` | Act 2 | Full cutover |
| `scenario/mirror-v2` | Act 2 | Shadow traffic — zero-risk validation |
| `scenario/incident-latency` | Act 3 | 1s latency injection |
| `scenario/incident-error` | Act 3 | 10% error rate injection |
| `scenario/quota-pressure` | Act 4 | Quota enforcement demo |
| `scenario/policy-enforce` | Act 4 | Gatekeeper deny mode |
| `scenario/load-off` | Closing | Safe shutdown |

Full scenario reference: `docs/DEMO-GUIDE.md §4`
