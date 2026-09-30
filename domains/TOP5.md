---
id: DOMAIN-TOP5
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: strategy-bound
canonical: true
---
# Top-5 Football

## CURRENT FACT

Top-5 production architecture and controlled activation routing are present in
main, but activation remains disabled by default and CEO-gated. The current
source contains the controlled activation routing contract at
`5f8523d7f5801ad9c5f9f4217699ea63ba54ed6e`.

## Contract

- `INITIAL` is the 22–26 hour planning path.
- `REFINEMENT` is the 60–120 minute path.
- The legacy 0–3 hour production path is not a valid replacement.
- Actionable odds freshness is at most 900 seconds.
- Closing odds are a benchmark, not an activation authority.
- Top-5 execution is a governed batch/publication path, not a free-running
  research loop.
- The five-fixture atomic batch contract must remain all-or-fail-closed.

## Readiness

The research gate is frozen separately from production activation. Provider
authority, quota, runtime evidence, canary, publication, and rollback gates
must all be independently satisfied. No note here grants activation.

See [[workstreams/TOP5-PRODUCTION]], [[workstreams/TOP5-SHADOW-READINESS]],
[[evidence/PR_EVIDENCE_INDEX]], and [[runbooks/top5-canary-preflight]].

## Related

- [[domains/DATA_AND_PROVIDERS]]
- [[domains/ODDS_AND_PROVIDERS]]
- [[domains/GOVERNANCE]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[decisions/records/DEC-0028]]
- [[decisions/records/DEC-0031]]
- [[components/CMP-PUBLICATION]]
- [[components/CMP-MONITORING]]
- [[runbooks/top5-rollback]]
