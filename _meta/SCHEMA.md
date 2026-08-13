---
type: "schema"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# Memory Schema

## Note classes

- `current-*` — hot operational truth
- `invariant-domain` — canonical invariant definitions
- `finding` — verified defect/risk/evidence item
- `decision` — explicit project/governance decision
- `workstream` — bounded improvement program
- `domain` — stable technical knowledge
- `historical-*` — cold evidence
- `builder-*` — task/context/report contract

## Finding statuses

- `open`
- `resolved_production`
- `resolved_branch_candidate`
- `superseded`
- `accepted_risk`

## Invariant statuses

- `enforced`
- `partial`
- `not_enforced`
- `unverified`
- `branch_candidate`
- `branch_partial`

## Freshness classes

- `stable`
- `release-bound`
- `runtime-sensitive`
- `historical`

## ID conventions

- Finding: `FND-YYYYMMDD-NNN`
- Decision: `DEC-NNNN`
- Incident: `INC-NNNN`
- Audit: `AUD-YYYYMMDD-NAME`
- Task: `TASK-<WORKSTREAM>-NNN`
- Prompt/task packet versions follow the Task ID.
