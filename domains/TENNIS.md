---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Tennis Domain

## Lifecycle

Canonical states:
`UPCOMING`, `AWAITING_START`, `DELAYED`, `LIVE`, `COMPLETED`, `POSTPONED`, `CANCELLED`, `UNKNOWN`.

Core rule: elapsed time alone never creates LIVE. LIVE requires qualified authoritative evidence.

## Schedule vs lifecycle

Initial schedule, current schedule and event lifecycle are separate concepts.

## Identity

Fixture registry solved important cross-midnight/reschedule issues but fallback identity still risks collisions across repeated event instances/year/round.

## Odds

Known open P0-quality semantic issue: non-H2H Tennis markets can receive H2H-B refresh quote. See FND-20260814-019.

## Sources

ESPN is used for strong live/completion evidence. TennisExplorer is supplemental/informational and must not silently promote its authority.

## Historical data

Some Tennis ledger rows are blank/wm2026 contaminated. New explicit sport/provenance is preferred; historical correction must be evidence-based.
