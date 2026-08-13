---
type: "builder-bootstrap"
tier: "hot"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# SportsBrain Builder Memory Rules

This directory is the SportsBrain shared memory.

**Do not recursively read the entire vault.**

Always start with:
1. `BOOTSTRAP.md`
2. `CURRENT_STATE.md`
3. `CURRENT_TASK.md`
4. `builder/CURRENT_CONTEXT_PACKET.md` if it exists and matches the current task ID.

Then inspect only the source files and adjacent callers/tests required by the task.

## Governance

- ChatGPT/CEO is read-only and independently audits your work.
- Claude is the normal Builder/source mutator.
- Do not merge without explicit later approval.
- No force push, destructive reset, or history rewrite.
- Preserve the user's original dirty worktree; use an isolated clean worktree.
- Do not weaken hard safety invariants.
- Stop and report if authority is ambiguous or the task expands into another P0 workstream.

## Context

Canonical specifications live under `invariants/`.
Architecture lives under `architecture/`.
Confirmed findings live under `findings/`.
Current workstream detail lives under `workstreams/`.

Historical files are evidence, not current truth.

## Final principle

Optimize for the invariant being true at the actual production boundary, not merely for a green test suite.
