---
id: JOB-LIVE-SCORE
type: job
title: live_score_push
status: observed
canonical: true
graph_domain: production
graph_role: operational
tier: warm
trigger_type: interval
schedule: "launchd 120s"
---
# live_score_push

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/PRODUCTION_OPERATIONS]]
- [[domains/PWA_AND_WORKER]]
- [[domains/MONITORING_AND_RECOVERY]]
- [[runbooks/worker-public-mismatch]]
