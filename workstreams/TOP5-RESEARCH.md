---
id: WS-TOP5-RESEARCH
type: workstream
tier: warm
status: final_audit_active
workstream: TOP5-RESEARCH
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: release-bound
---
# Top-5 Research

Builder A is Research Owner. The generic five-league framework and frozen BL1
v7 baseline are present in the SportsBrain research branch. Required gates
include true A/B/A' contamination, expanded structural invariants, BL1 parity,
statistics correction, no sealed-data access, and no fishing or tuning.

DEV/CALIB/HOLDOUT semantics remain explicit: DEV is the research decision
population, CALIB=2425 and HOLDOUT=2526 remain sealed, and LIVE_SHADOW=2627 is
deferred. The evidence supports no deployable-edge claim without the required
signal-time, provider, shadow, and rollout gates. The final audit remains an
active CEO gate even though the baseline framework is complete.
