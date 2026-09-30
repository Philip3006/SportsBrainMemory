---
id: JOB-ODDS-REFRESH
type: job
title: odds_refresh
status: observed
canonical: true
graph_domain: providers-data
graph_role: operational
tier: warm
trigger_type: interval
schedule: "launchd 300s"
---
# odds_refresh

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/DATA_AND_PROVIDERS]]
- [[domains/ODDS_AND_PROVIDERS]]
- [[domains/TOP5]]
- [[runbooks/stale-odds]]
- [[runbooks/quota-evidence-failure]]
