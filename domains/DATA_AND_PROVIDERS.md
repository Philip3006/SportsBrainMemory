---
id: DOMAIN-DATA-PROVIDERS
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: release-bound
canonical: true
---
# Data & Providers

## CURRENT FACT

Provider identity is evidence, not a repository default. Every provider result
must retain source, request scope, fixture identity, timestamp, and market
provenance. Missing or conflicting evidence fails closed.

## Rules

- `the_odds_api` remains the production authority in the current merged path;
  iSports is candidate/shadow-only where the source contract says so.
- Exact native fixture IDs bind schedule, odds, model, and publication records.
- No provider call is inferred from a cached file or a memory note.
- Quota pauses are distinct from normal attempts and dead-letter budgets.
- Freshness is bounded per surface; actionable odds use the 900-second rule.
- Historical datasets require provenance, temporal-integrity evidence, and a
  reproducible digest.

See [[domains/ODDS_AND_PROVIDERS]], [[architecture/DATA_AND_PERSISTENCE]], and
[[runbooks/quota-evidence-failure]].

## Related

- [[domains/TOP5]]
- [[domains/NATIONS_LEAGUE]]
- [[domains/TENNIS]]
- [[providers/PRV-WORKER]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[runbooks/provider-auth-failure]]
- [[runbooks/stale-odds]]
- [[runbooks/historical-research-data-ingestion]]
- [[decisions/records/DEC-0031]]
