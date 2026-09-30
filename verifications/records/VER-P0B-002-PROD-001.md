---
id: VER-P0B-002-PROD-001
type: verification
title: P0-B2 Schedule & Window Truth production verification
status: verified
canonical: true
graph_domain: production
graph_role: evidence
tier: warm
created_at: 2026-08-17T17:00:00+02:00
updated_at: 2026-08-17T17:00:00+02:00
freshness_class: release-bound
verification_status: verified
evidence:
  - EVD-P0B-002-PROD-001
workstream: P0-B
findings:
  - FND-20260814-006
  - FND-20260814-008
  - FND-20260814-009
  - FND-20260814-010
---
# P0-B2 Schedule & Window Truth — Production Verification

**TASK-P0B-002 is CLOSED / production verified.**

Machine-readable `JobExpectation` semantics now govern all monitoring expectations with timezone-correct cron evaluation. Windowed BL2 jobs publish `expectation_state=not_expected` when off-window instead of false stale. launchd calendar jobs use `tz="Europe/Berlin"` with DST-correct `zoneinfo` evaluation. Tennis scan expects 8 points/day UTC. The event-driven consumer uses `EventWithFallbackExpectation`. Odds refresher is registered in aggregate health coverage. `reported_status` enables lossless baseline round-trips. Verified via [[evidence/records/EVD-P0B-002-PROD-001]].
