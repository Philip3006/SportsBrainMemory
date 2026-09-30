---
id: DOMAIN-PRODUCT-CONTRACT
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: stable
canonical: true
graph_domain: product
graph_role: core
---
# Product Contract

## CURRENT FACT

The PWA is a public read surface for sports schedules, signals, model views,
and shadow evidence. It is not an authority boundary for betting, activation,
or ledger mutation.

## Semantics

- A probability is a model output; confidence is evidence quality and must not
  be conflated with probability.
- A signal is actionable only when the full freshness, identity, provider,
  market, model, risk, and activation gates pass.
- `SHADOW_ONLY`, `WEAK_EVIDENCE_SHADOW_ONLY`, and `no_bet=true` are explicit
  non-actionable states.
- A Nations League shadow fixture may be visible without becoming an
  actionable Football bet.

## UX ownership

The PWA owns presentation and navigation. The Worker/public serializer owns
the public/private boundary. Provider adapters and the ledger remain outside
the UI's authority. Product instrumentation follows the centralized
`sbAnalytics` abstraction described by PR #221; that implementation is
branch-only until merged/deployed.
