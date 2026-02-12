# Scenarios

## Core
- `scenario/baseline`: normal app, weight-0, load baseline
- `scenario/load-off`: normal app, weight-0, load disabled
- `scenario/load-peak`: normal app, weight-0, high load

## Progressive delivery
- `scenario/canary-10`: normal app, weight-10, baseline load
- `scenario/canary-50`: normal app, weight-50, baseline load
- `scenario/canary-100`: normal app, weight-100, baseline load

## Incident drills
- `scenario/incident-latency`: latency fault in payment-mock v2, weight-10, baseline load
- `scenario/incident-error`: error fault in payment-mock v2, weight-10, baseline load

## Optional
- `scenario/mirror-v2`: mirror to v2, baseline load