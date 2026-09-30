---
id: JOB-CONSUME
type: job
title: consume_pending_bets
status: observed
canonical: true
tier: warm
trigger_type: event_with_fallback
schedule: "Worker dispatch + 30m GHA fallback"
---
# consume_pending_bets

Observed execution expectation from the P0-B source audit. P0-B implementation must reconcile this record against active workflow/launchd source at task start.

## Related

- [[domains/LEDGER_AND_MEASUREMENT]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[components/CMP-BETTING]]
- [[writers/WRT-FINANCIAL]]
