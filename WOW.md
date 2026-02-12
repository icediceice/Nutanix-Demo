# WOW Spec

## Objective
Boost audience impact by adding executive KPI visibility and governance proof without changing branch-driven demo operations.

## KPI Board
- refresh_interval_seconds: 5
- panels:
  - name: Flux Success Rate
    source: flux kustomization ready ratio
    threshold: ">= 90%"
    status_rules:
      - good: ">= 90%"
      - warn: ">= 70% and < 90%"
      - bad: "< 70%"
  - name: Canary Weight v2
    source: istio virtualservice frontend route weights
    threshold: "informational"
    status_rules:
      - good: "0-100 (info)"
  - name: Policy Compliance
    source: policyreports/clusterpolicyreports summary
    threshold: ">= 95%"
    status_rules:
      - good: ">= 95%"
      - warn: ">= 85% and < 95%"
      - bad: "< 85%"
  - name: Rollback SLA Target
    source: static target
    threshold: "< 3 minutes"
    status_rules:
      - good: "target met during demo drill"

## Policy Gate
- engine: Kyverno
- mode: Audit (non-blocking for demos)
- rules:
  - name: require-standard-labels
    scope: demo-app,demo-ops
    enforce: audit
    checks:
      - metadata.labels.app exists
      - metadata.labels.version exists
  - name: require-requests-limits
    scope: demo-app,demo-ops
    enforce: audit
    checks:
      - resources.requests.cpu/memory
      - resources.limits.cpu/memory
  - name: disallow-latest-tag
    scope: demo-app,demo-ops
    enforce: audit
    checks:
      - container image must not end with :latest

## Demo Script Impact
- Show branch switch on demo wall
- Show canary weight shifting on demo wall and Kiali
- Show policy summary panel and one warning example
- Show rollback target card as operational objective

## Acceptance Criteria
- demo wall displays KPI cards with status colors
- demo wall displays policy pass/warn/fail summary
- Flux and scenario behavior remain unchanged
- policies are audit-only and namespace-scoped to demo namespaces
