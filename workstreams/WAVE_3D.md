---
id: WS-WAVE3D
type: "workstream"
tier: "warm"
status: "planned"
workstream: "WAVE-3D"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Wave 3D — Production Trust Monitor

## Objective

Produce one semantic trust artifact with:
- `HEALTHY`
- `DEGRADED`
- `UNSAFE`
- `UNKNOWN`.

## Planned checks

- actionable + stale/missing/current-odds mismatch
- absurd EV
- >5% stake / >3 active bets
- false Tennis LIVE
- open Tennis bet missing from live monitor
- schedule authority contradiction
- fixture collision
- Worker/GitHub state divergence
- source-release/CI mismatch
- public schema/private-data violation
- provider/odds freshness
- canonical bet provenance.

Do not implement before the semantics being monitored are corrected.
