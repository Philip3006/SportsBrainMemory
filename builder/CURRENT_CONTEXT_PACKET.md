# SportsBrain V1 Context Packet

Task: TASK-P0B-001
Task status: approved
Budget class: standard

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

---
id: TASK-P0B-001
type: task
title: Execution Truth
status: approved
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T14:00:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-005
invariants:
  - MON-001
  - MON-011
  - OPS-006
source_paths:
  - src/monitoring/health_writer.py
  - src/monitoring/aggregate_health.py
  - tests/monitoring/test_health_truth.py
---
# TASK-P0B-001 — Execution Truth

## Mission

Make execution status derive from execution evidence so `exit_code != 0` can never publish success.

## Primary files / boundaries

- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/test_health_truth.py`

## Adjacent read-only inspection

- `.github/workflows/*health*`
- `.github/workflows/*retrain*`
- `.github/workflows/*closing*`

## Forbidden scope

- schedule redesign
- privacy migration
- writer governance
- model changes

## Deterministic gates

- non-zero exit cannot serialize execution success
- malformed/unknown execution fails closed
- existing valid success/degraded cases remain deterministic
- focused + full monitoring tests

## Production verification

- published health contains no `ok + exit_code!=0` state
- exact source SHA and runtime-data SHA reported separately

## Rollback

Revert execution-truth helper/writer changes together; do not roll back unrelated runtime data.

## STOP conditions

- runner context cannot supply truthful exit evidence
- required workflow semantics differ materially from scoped model

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.


## Required invariants

- MON-001
- MON-011
- OPS-006

## FND-20260814-005

---
type: "finding"
tier: "warm"
id: "FND-20260814-005"
status: "open"
severity: "P0"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-001
  - MON-011
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-005 — Health can report status=ok with exit_code=1

## Problem / evidence

Health writer accepts caller status and exit code independently; public health has shown impossible green/failure combinations.

## Failure / impact

Operational dashboard can be falsely green during job failure.

## Required closure

Derive execution truth; non-zero exit can never be service OK.

## Related invariants

- `MON-001`
- `MON-011`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## External source scope

- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/test_health_truth.py`
