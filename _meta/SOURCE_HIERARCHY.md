---
type: "meta-policy"
tier: "warm"
status: "active"
last_updated: "2026-09-30T12:46:53+02:00"
freshness_class: "stable"
---
# Source / Evidence Hierarchy

SportsBrain memory is an operational index, not a substitute for the system
that produced the evidence. When two sources disagree, the stronger source
wins and the discrepancy is recorded rather than silently rewritten.

## Precedence

1. **Bounded production/runtime evidence** — timestamped observations from the
   governed endpoint, deployment, process, database, or artifact boundary.
2. **Fresh `origin/main`** — the exact source tree and configuration at the
   SHA actually inspected; runtime/data commits do not become source-release
   claims.
3. **Exact-head CI and merged PR evidence** — only the tested head is valid;
   an open or branch-only PR is not production truth.
4. **Canonical datasets and provenance** — immutable snapshots, source
   digests, temporal-integrity evidence, and explicit dataset ownership.
5. **Approved decisions / ADRs** — the governing design choice, including its
   scope and expiry or supersession.
6. **Operational Memory** — current-state cards, indexes, and runbooks that
   point back to the stronger sources above.
7. **Historical records** — preserved context, incidents, and superseded
   findings; useful for why, never sufficient for what is live now.
8. **Hypotheses and ideas** — explicitly non-authoritative until verified.

## Required labels

Important notes must make their epistemic status obvious:

- `CURRENT FACT` — current and directly supported by a listed source.
- `VERIFIED RESULT` — a bounded test or observation with evidence.
- `DECISION` — an approved rule or architecture choice.
- `BLOCKER` — an unmet gate that stops a defined path.
- `HYPOTHESIS` — proposed work or interpretation, not a fact.
- `SUPERSEDED` — retained history replaced by a newer canonical record.
- `HISTORICAL CONTEXT` — preserved background without current authority.

## Conflict procedure

1. Record both claims and their source SHAs/timestamps.
2. Prefer the highest applicable precedence above.
3. Mark the weaker claim `SUPERSEDED`, `BRANCH CANDIDATE`, or
   `UNVERIFIED`; do not delete valuable history.
4. Update only the canonical owner and regenerate projections.
5. Re-run the Memory validator before committing.
