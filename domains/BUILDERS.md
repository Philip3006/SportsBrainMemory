---
id: DOMAIN-BUILDERS
type: domain
tier: hot
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Builders & Workstreams

## CURRENT FACT

CODEX is the sole SportsBrain builder platform. The versioned Memory V2
packets currently model Builder 1/2/3; the newer operational dispatch policy
also describes Builder 4/5 lanes. Until a source-backed role registry is
merged, Builder 4/5 ownership is recorded here as a governance gap rather
than invented as an active assignment.

## Ownership map

| Lane | Current scope | Safe continuation |
|---|---|---|
| Builder 1 | Top-5 shadow integration / evidence | Shadow-only, exact artifacts |
| Builder 2 | Top-5 production and activation readiness | Prepare; never self-activate |
| Builder 3 | Memory / Obsidian / observability | Canonical records, validators, packets |
| Builder 4 | Provider/Top-5 execution lane in current dispatch policy | CEO-gated, no duplicate authority |
| Builder 5 | Dependency coordination / dispatcher lane in current policy | Coordination only; no provider duplication |

## Dependency and overlap rules

- One workstream has one owner and one canonical evidence path.
- A worker may continue routine same-lane work, testing, documentation, and
  safe PR updates without routine approval.
- New provider authority, paid quota, production activation, betting/ledger
  authority, public publication, destructive runtime mutation, and merge gates
  remain explicit CEO gates.
- Existing historical PRs are not blindly merged; required behavior is
  ported to current main and exact-head CI is retained.

Current PR and evidence ownership is indexed at
[[evidence/PR_EVIDENCE_INDEX]]. Onboarding starts at
[[builder/ONBOARDING_30_MIN]].
