---
id: DOMAIN-GOVERNANCE
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: stable
canonical: true
graph_domain: governance
graph_role: core
---
# Governance & Safety

## DECISION

SportsBrain fails closed at authority boundaries. Research, shadow, public
presentation, activation, publication, betting, ledger mutation, scheduler
mutation, and deployment are separate permissions.

## Non-negotiables

- No automatic promotion from research or shadow to production.
- No provider authority from a repository constant alone.
- No secret material in Memory, logs, public artifacts, or evidence summaries.
- No merge without exact relevant CI and explicit approval where required.
- No historical record is rewritten to make a newer state look older or
  better.
- A blocked gate is a state to preserve, not a reason to guess.

See [[_meta/SOURCE_HIERARCHY]], [[_meta/MEMORY_RULES]],
[[architecture/TRUTH_AND_WRITERS]], and [[runbooks/incident-triage]].
