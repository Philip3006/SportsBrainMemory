---
id: TASK-MEM-V2-001
type: task
title: Memory V2 Live Obsidian System
status: active
canonical: true
tier: warm
workstream: MEMORY-V2
builder: Builder 3
builder_number: 3
created_at: 2026-09-13T22:40:00+02:00
updated_at: 2026-09-13T23:34:53+02:00
freshness_class: stable
budget_class: complex
findings:
  - FND-MEMORY-V2-001
invariants:
  - MEM-001
  - MEM-002
  - MEM-003
source_paths:
  - tools/memorylib/v2.py
  - tools/sync_memory.py
  - _live/
---
# TASK-MEM-V2-001 — Memory V2 Live Obsidian System

## Mission

BUILDER: 3

Maintain reviewed canonical Memory while exposing a near-live operational
view in Obsidian without runtime-noise commits or unsafe synchronization.

## Required gates

- canonical event validation and idempotency;
- pending Builder evidence never becomes approved truth automatically;
- generated views and bounded packets are deterministic;
- sync is fetch + fast-forward only and blocks local Vault edits;
- no SportsBrain production, Cloudflare, financial ledger, or sealed research mutation.

## CEO gate

Implementation is ready for CEO review. The branch must not be merged until
the CEO accepts the canonical backfill, the user-level sync behavior, and the
remaining unresolved remote/launchd limitations recorded in the handoff.
