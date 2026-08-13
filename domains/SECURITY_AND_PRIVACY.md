---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Security & Privacy

## Current architecture risk

The public repository and public/static signals paths expose personal financial/betting state. The unauthenticated Worker default snapshot architecture can also blur user isolation.

## P0-C target

- public product snapshot: fixtures/signals/odds/live/public health only
- authenticated private user state: bankroll/open/settled/history
- no default-user private fallback
- explicit owner identity
- private durable ledger store
- public artifact allowlist
- privacy text matches deployed reality.

## Memory security

This Memory stores these risks and architecture facts, not actual private ledger rows, credentials or tokens.
