---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Odds & Providers

## Refreshed odds authority

`data/cache/odds_state.json` is designed as the single local authority for refreshed odds.

Stored concepts include:
- initial/current odds
- initial/current EV
- odds timestamp
- source/tier
- signal lifecycle
- odds history.

## Freshness

Canonical hard stale window for Value actionability is 30 minutes.

## Provider principle

A provider may have different authority by concept:
fixture existence, schedule, live lifecycle, result, current market quote.

## Market correctness

The exact quote must correspond to the exact signal market/selection. Nearby H2H pricing is not a valid substitute for totals/set handicap/side markets.

See FND-20260814-019 and FND-20260814-026.
