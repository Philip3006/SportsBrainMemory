---
type: builder-contract
tier: hot
status: active
---
# Claude Builder Runbook

## Session contract

- One scoped Builder task per session unless the task explicitly authorizes a combined unit.
- Start from the generated Context Packet; inspect only primary and adjacent-read scope unless a STOP condition requires escalation.
- Never invent a new product/architecture decision silently. STOP and report the missing decision.
- Local deterministic gates before push; exact-head CI after push; production evidence before closure.
- Builder may report `implementation_complete`; it does not close production findings by assertion.

## Recommended sequence after Memory V1 acceptance

1. TASK-P0B-001
2. TASK-P0B-002
3. TASK-P0B-003
4. TASK-P0B-004
5. TASK-P0C-001
6. TASK-P0C-002
7. TASK-P0D-001
8. TASK-P0D-002
9. TASK-P0D-003
10. TASK-MODEL-001
11. TASK-MEAS-001
12. TASK-MODEL-002

Do not combine financial durability, AI source-governance, or model promotion with unrelated tasks.
