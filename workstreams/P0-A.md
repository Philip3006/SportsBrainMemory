---
type: "workstream"
tier: "hot"
status: "open"
workstream: "P0-A"
last_updated: "2026-08-14T01:06:00+02:00"
verified_against_pr_head: "08b63f8a14fb64021f79277e7069e9aee11327f9"
freshness_class: "runtime-sensitive"
---
# P0-A — Canonical Betting Safety

Mission: one end-to-end actionability/risk contract across PWA → Worker → queue → Consumer → Ledger.

**OPEN. DO NOT MERGE.**

Reviewed head: `08b63f8a14fb64021f79277e7069e9aee11327f9`  
Exact-head CI: GREEN (`31752148258`), but Playwright is not part of this CI workflow.

Current blockers:
- [[findings/records/FND-20260814-001]]
- [[findings/records/FND-20260814-002]]
- [[findings/records/FND-20260814-003]]
- [[findings/records/FND-20260814-004]]
- [[findings/records/FND-20260814-030]]
- [[findings/records/FND-20260814-031]]

Current task: `TASK-P0A-010`.

Closure requires all six blockers, complete Playwright green, Node/Ruff/Python green, exact new-head CI green, CEO review, then a separate merge approval. Post-merge verification is required before P0-B.
