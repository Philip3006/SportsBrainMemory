---
id: TASK-MEM-V1-ACCEPT
type: task
title: Memory V1 Installation Acceptance
status: completed
canonical: true
tier: warm
workstream: MEMORY_V1
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T14:00:00+02:00
freshness_class: release-bound
budget_class: standard
source_paths:
  - SportsBrainMemory repository only
---
# TASK-MEM-V1-ACCEPT — Memory V1 Installation Acceptance

## Mission

Install this already-built V1 package into SportsBrainMemory only, preserve backup, run full acceptance, and report exact diff. Do not alter SportsBrain.

## Primary files / boundaries

- `SportsBrainMemory repository only`

## Adjacent read-only inspection

- `all V1 package files`

## Forbidden scope

- SportsBrain product repository
- P0-B implementation
- any deployment

## Deterministic gates

- installer dry-run
- backup exists
- python compileall
- full Memory acceptance suite
- strict validator 0 errors/warnings
- generated-view drift check
- context preview checks
- fresh ZIP/package fingerprint comparison

## Production verification

- Obsidian HOME opens from installed repository
- CURRENT_TASK says NONE
- Memory repo remains semantically green

## Rollback

Restore timestamped full backup of every replaced file; never use destructive reset.

## STOP conditions

- Memory repo baseline differs unexpectedly from documented V0 baseline
- dirty local work could be overwritten
- any acceptance gate fails

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
