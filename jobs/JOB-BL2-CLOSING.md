---
id: JOB-BL2-CLOSING
type: job
title: bundesliga2_closing_odds
status: observed
canonical: true
graph_domain: production
graph_role: operational
tier: warm
trigger_type: cron_set
schedule: "four weekly pre-kickoff points"
---
# bundesliga2_closing_odds

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/FOOTBALL]]
- [[domains/ODDS_AND_PROVIDERS]]
- [[runbooks/stale-odds]]
- [[workstreams/P0-B]]
