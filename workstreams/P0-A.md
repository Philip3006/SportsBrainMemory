---
type: "workstream"
tier: "hot"
status: "open"
workstream: "P0-A"
last_updated: "2026-08-14T00:03:00+02:00"
verified_against_pr_head: "f2f7831fdaead6667b6eb53c0021a7bc0377eebf"
freshness_class: "runtime-sensitive"
---
# P0-A — Canonical Betting Safety

## Mission

Create one end-to-end betting actionability/risk contract across PWA → Worker → queue → Consumer → Ledger.

## What has improved on the candidate branch

- canonical signal resolution
- strict `value|manual`
- current odds/freshness
- sport-aware Tennis event state
- 5% cap and max-three controls
- explicit ledger identity/provenance
- model probability normalization
- Worker contract tests in CI
- risk heartbeat
- improved placement durability ordering.

## Status

**OPEN. DO NOT MERGE.**

Exact reviewed head: `f2f7831fdaead6667b6eb53c0021a7bc0377eebf`  
Exact-head CI: GREEN (`31741469276`).

## Current merge blockers

- [[findings/records/FND-20260814-001]]
- [[findings/records/FND-20260814-002]]
- [[findings/records/FND-20260814-003]]
- [[findings/records/FND-20260814-004]]

## Closure gate

1. Fix all four current findings.
2. Real deterministic durability tests.
3. Real mandatory Playwright submit.
4. Exact new PR-head CI green.
5. CEO independent read-only review.
6. Merge only after approval.
7. Post-merge source + exact main CI.
8. Worker/public data/PWA verification.
9. Only then mark P0-A closed and start P0-B implementation.
