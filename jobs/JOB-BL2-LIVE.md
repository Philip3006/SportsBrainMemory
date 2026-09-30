---
id: JOB-BL2-LIVE
type: job
title: bundesliga2_live_push
status: observed
canonical: true
graph_domain: production
graph_role: operational
tier: warm
trigger_type: windowed_interval
schedule: "Fri 18-22; Sat/Sun 11-22 UTC, 2m"
---
# bundesliga2_live_push

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/FOOTBALL]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[domains/MONITORING_AND_RECOVERY]]
- [[workstreams/P0-B]]
