---
type: "current-blockers"
tier: "hot"
status: "current"
last_updated: "2026-08-14T01:31:00+02:00"
freshness_class: "runtime-sensitive"
workstream: "P0-A"
---
# Current Blockers

Merge blockers after CEO review of PR #10 head `a90be4c492b736b348dba9b3847c3b1d9823031a`:

1. [[findings/records/FND-20260814-001]] — staged-diff Git error (`rc>1`) is not explicitly fail-closed.
2. [[findings/records/FND-20260814-003]] — clear-all cancellation ACK can lose unresolved/concurrent cancellation intents; mixed test is insufficient.
3. [[findings/records/FND-20260814-031]] — incomplete canonical cards and model-tip recommendations still auto-create Manual betting actions.

Resolved in this review: FND-002, FND-004, FND-030.

No merge until all three blockers close, all required tests are green, exact new-head CI is green and CEO re-verifies.
