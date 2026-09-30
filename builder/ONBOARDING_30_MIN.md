---
id: BUILDER-ONBOARDING-30MIN
type: builder-entry
tier: hot
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: stable
canonical: true
graph_domain: memory
graph_role: support
---
# New Builder — 30-Minute Onboarding

## First five minutes

1. Read [[00_HOME]] and [[_meta/SOURCE_HIERARCHY]].
2. Read [[CURRENT_STATE]] and [[CURRENT_BLOCKERS]].
3. Identify the exact current `origin/main` SHA and whether your target PR is
   merged, open, or branch-only.

## Next ten minutes

4. Open the relevant domain note: [[domains/TOP5]],
   [[domains/NATIONS_LEAGUE]], [[domains/PRODUCTION_OPERATIONS]],
   [[domains/MODEL_RESEARCH]], or [[domains/TENNIS]].
5. Read the linked ADRs and the exact PR/evidence entry.
6. Check the corresponding runbook before touching a boundary.

## Final fifteen minutes

7. Confirm inputs, owner, dependency, forbidden scope, and abort condition.
8. Keep source-release SHA distinct from runtime/data SHA.
9. Preserve secrets, private state, historical evidence, and unrelated dirty
   files.
10. Return a bounded handoff with tests, exact SHA, evidence, and remaining
    blocker. Do not merge or activate without the applicable gate.
