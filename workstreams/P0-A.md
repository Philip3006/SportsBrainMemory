---
type: "workstream"
tier: "hot"
status: "open"
workstream: "P0-A"
last_updated: "2026-08-14T01:31:00+02:00"
verified_against_pr_head: "a90be4c492b736b348dba9b3847c3b1d9823031a"
freshness_class: "runtime-sensitive"
---
# P0-A — Canonical Betting Safety

**OPEN. DO NOT MERGE.**

Reviewed head: `a90be4c492b736b348dba9b3847c3b1d9823031a`  
Exact-head CI: GREEN (`31753905213`).

TASK-P0A-010 closed FND-002, FND-004 and FND-030, but CEO review found three remaining blockers:
- [[findings/records/FND-20260814-001]]
- [[findings/records/FND-20260814-003]]
- [[findings/records/FND-20260814-031]]

Current Builder task: `TASK-P0A-011`.

Closure requires exact cancellation-intent ACK semantics, no recommendation→Manual downgrade, final Git fail-closed semantics, all local gates, exact new-head CI green, then independent CEO review. Merge remains a separate explicit decision followed by post-merge production verification.
