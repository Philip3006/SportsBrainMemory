---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Football Domain

SportsBrain contains multiple Football contexts including tournament-era/WM tooling, Bundesliga 2, Dixon-Coles, Elo, LGBM/stacking and special-market/scorer layers.

Core flow:
data/fixture universe → model probabilities → gates → market odds → canonical signal → publication/actionability → ledger/settlement/measurement.

Key rule:
informational model tips or match-detail views cannot create canonical Value semantics independently from the registered signal contract.
