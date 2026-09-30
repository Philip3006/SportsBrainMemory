---
id: JOB-TENNIS-CLOSING
type: job
title: tennis_closing_odds
status: observed
canonical: true
graph_domain: tennis
graph_role: operational
tier: warm
trigger_type: interval
schedule: "30m + manual"
---
# tennis_closing_odds

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/TENNIS]]
- [[domains/DATA_AND_PROVIDERS]]
- [[runbooks/stale-odds]]
- [[workstreams/P0-B]]
