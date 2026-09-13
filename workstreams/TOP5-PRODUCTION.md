---
id: WS-TOP5-PRODUCTION
type: workstream
tier: warm
status: completed_disabled
workstream: TOP5-PRODUCTION
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: release-bound
---
# Top-5 Production Architecture

PR #54 is retained as the safe historical baseline. PR #55 merged at
`b4d6765f79b20ca2f2c3d3b323ee2f666a1449ad` and completed the generic Top-5
production architecture reconciliation.

The architecture is disabled by default, has cumulative rollout evidence
gates, no active Top-5 registration, no bound production model, and no live
provider/scheduler/publisher/Cloudflare/ledger path. Closing odds remain a
benchmark/CLV artifact and cannot enter prediction inputs.
