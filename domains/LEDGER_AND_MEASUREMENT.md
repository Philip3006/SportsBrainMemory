---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Ledger & Measurement

## Ledger

Current architecture uses per-user CSV as the primary financial record with SQLite as a secondary representation.

P0-A adds stronger explicit fields such as:
- sport
- league
- signal_id
- fixture_key
- bankroll_at_placement
- stake_pct
- model_prob provenance.

## Measurement problem

Historical `source=value` is not sufficient proof that a bet passed the canonical production signal contract. Tennis classification also historically inferred sport from market/source/league.

Therefore historical ROI/Brier/ECE/CLV must be interpreted cautiously.

## Target

New production metrics classify from explicit immutable provenance.
Historical reclassification uses evidence manifests; UNKNOWN remains UNKNOWN.

Closing odds must match exact entry proposition before CLV is trusted.
