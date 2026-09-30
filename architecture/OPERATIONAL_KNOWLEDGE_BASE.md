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
