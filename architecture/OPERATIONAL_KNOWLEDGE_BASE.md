---
id: ARCH-OPERATIONAL-KB
type: architecture
tier: hot
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: stable
canonical: true
---
# SportsBrain Operational Knowledge Base

## CURRENT FACT

This note is the navigation contract for the private SportsBrain Memory. It
does not own volatile production values; those live in the current state card,
bounded evidence records, and the source/runtime systems named below.

## Two-minute orientation

SportsBrain is a governed sports analytics product with a public PWA, a
Cloudflare Worker/public-snapshot boundary, provider adapters, model/research
pipelines, and a separately governed betting/ledger path. Production,
shadow/research, and historical evidence are intentionally separate.

- **Live/public:** the PWA and Worker/public data path already merged to main;
  see [[domains/PRODUCTION_OPERATIONS]] and [[domains/PWA_AND_WORKER]].
- **Shadow/research:** Nations League public shadow evidence remains
  non-actionable; see [[domains/NATIONS_LEAGUE]].
- **Top-5:** production architecture is disabled by default; see
  [[domains/TOP5]].
- **Current operational state:** [[state/records/STATE-20260930-001]] and
  [[CURRENT_STATE]].
- **Current blockers:** [[CURRENT_BLOCKERS]] and [[runbooks/INDEX]].
- **Builder onboarding:** [[builder/ONBOARDING_30_MIN]] and
  [[domains/BUILDERS]].

## Read in this order

1. [[00_HOME]]
2. [[_meta/SOURCE_HIERARCHY]]
3. [[CURRENT_STATE]]
4. The relevant domain MOC under [[mocs/Architecture]] or [[mocs/Memory]]
5. The exact evidence/PR entry in [[evidence/PR_EVIDENCE_INDEX]]
6. The relevant runbook before touching a live boundary

Supporting indexes: [[architecture/INDEX]], [[builder/INDEX]],
[[decisions/INDEX]], [[evidence/INDEX]], [[findings/INDEX]],
[[invariants/INDEX]], [[jobs/INDEX]], [[providers/INDEX]],
[[tasks/INDEX]], [[verifications/INDEX]], [[workstreams/INDEX]], and
[[writers/INDEX]]. Event protocol: [[events/README]].

## Knowledge areas

| Area | Canonical entry | Current boundary |
|---|---|---|
| Product/PWA | [[domains/PRODUCT_CONTRACT]] | Public UX and semantics; no private authority |
| Production/operations | [[domains/PRODUCTION_OPERATIONS]] | Runtime evidence, Worker, Pages, monitoring |
| Top-5 football | [[domains/TOP5]] | Disabled-by-default, CEO-gated activation |
| Nations League | [[domains/NATIONS_LEAGUE]] | Shadow/public non-actionable evidence |
| Tennis | [[domains/TENNIS]] | Existing live/settlement path and known risks |
| Models/research | [[domains/MODEL_RESEARCH]] | Evidence, calibration, promotion gates |
| Data/providers | [[domains/DATA_AND_PROVIDERS]] | Identity, freshness, quota, provenance |
| Governance/safety | [[domains/GOVERNANCE]] | Fail-closed authority and mutation boundaries |
| Builders | [[domains/BUILDERS]] | Ownership, dependencies, handoff rules |

## What is intentionally not here

No API keys, bearer tokens, private ledger rows, bankroll state, hidden
authorization payloads, or unverified production claims belong in Memory.
Public client configuration may be described as architecture, but values are
kept out of the vault unless they are explicitly intended as public product
configuration.

## Canonical vault contract

The authoritative vault is `/Users/philiprassillier/SportsBrain-Memory`.
The Obsidian mirror is `/Users/philiprassillier/Downloads/SportsBrain-Memory`.
The canonical Git repository is the source of truth whenever their contents
diverge. Sync flows from canonical Git to the mirror through the existing
user-level synchronizer; `.obsidian/` configuration and mirror-only edits are
not canonical records.

For an update, fetch and inspect the canonical repository, update one
canonical record, render generated views, run the local validators/tests,
review the Memory-only diff, and open one narrow PR. After review, sync the
mirror and confirm the synchronizer's manifest/revision and conflict checks.
If either side is dirty or divergent, preserve both copies and stop for an
explicit conflict resolution. Nothing may write from the mirror back to the
canonical repository automatically unless that write-back is explicitly
intended and reviewed.

The current Memory repository `main` observed for PR #10 retargeting is
`7a3bef352bce88856c785ded519b4e3775980d7d`; the retargeted PR merge base is
that same SHA. This is Memory-repository provenance and must not be confused
with the SportsBrain source/runtime SHAs in [[CURRENT_STATE]].
