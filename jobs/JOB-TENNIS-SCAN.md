---
id: JOB-TENNIS-SCAN
type: job
title: tennis_scan
status: observed
canonical: true
graph_domain: tennis
graph_role: operational
tier: warm
trigger_type: cron_set
schedule: "02,06,09,12,15,18,21,23 UTC"
---
# tennis_scan

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/TENNIS]]
- [[domains/DATA_AND_PROVIDERS]]
- [[domains/ODDS_AND_PROVIDERS]]
- [[runbooks/stale-odds]]
