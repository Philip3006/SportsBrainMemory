---
id: PR10-RETARGET-EVIDENCE
type: evidence
tier: hot
status: current
last_updated: 2026-09-30T13:35:08+02:00
freshness_class: release-bound
canonical: true
---
# PR #10 Retarget Evidence

## VERIFIED RESULT

PR #10 remains the single operational-knowledge-base PR. It is retargeted to
the current default branch `main`; no replacement PR was created and no merge
was performed.

- Current Memory `main`: `7a3bef352bce88856c785ded519b4e3775980d7d`
- New merge base: `7a3bef352bce88856c785ded519b4e3775980d7d`
- Original feature-base branch: `feat/memory-v2-live-obsidian`
- PR state: open / not merged
- Repository CI before this change: no checks configured

The branch history was cleaned by replaying only the operational-KB commit
onto current `main`. The prior Memory-V2 feature commits are not replayed as
new PR changes. The retargeted diff contains the operational navigation,
evidence, runbook, template, validator, state-reconciliation, and local-CI
changes only; it does not include the old Memory-V2 implementation files such
as `tools/memorylib/v2.py`, `tools/memorylib/live.py`, or
`tests/test_memory_v2.py`.

The exact current PR head is always taken from PR metadata and reported in the
handoff; this note records the verified base and merge-base boundary.
