---
id: WS-TOP5-RESEARCH
type: workstream
tier: warm
status: completed_ceo_approved
workstream: TOP5-RESEARCH
input_owner: Builder 1
frozen_research_sha: 6eaabbec7d0182103d815c72fae4976e261b40aa
last_updated: 2026-09-13T23:34:53+02:00
freshness_class: release-bound
---
# Top-5 Research — COMPLETE / CEO APPROVED

The final Research Gate is CEO approved at frozen SHA
`6eaabbec7d0182103d815c72fae4976e261b40aa`. Top-5 development is complete;
the result is now immutable input to Builder 1 Shadow Integration.

DEV/CALIB/HOLDOUT semantics remain explicit: DEV is the research decision
population, CALIB=2425 and HOLDOUT=2526 remain SEALED, and LIVE_SHADOW=2627 is
deferred. Research completion does not approve a model or betting strategy for
production. Builder 1 may consume this immutable input only for Research →
NO-BET Shadow Integration.
