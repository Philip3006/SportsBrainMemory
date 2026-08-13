---
type: "memory-home"
tier: "hot"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# SportsBrain Shared Memory

This repository is the **canonical shared knowledge layer** for SportsBrain.

It is designed for three readers:

- **ChatGPT / CEO** — read-only audit, architecture, prioritization, merge decisions.
- **Claude / Builder** — selective task context and implementation instructions.
- **Human / Owner** — Obsidian view, version history, review and final authority.

## Core rule

> **Store everything important. Load only what the current task needs.**

The Memory is not production truth by itself. Current repository/runtime evidence outranks Memory when they conflict.

## Start here

- [[BOOTSTRAP]]
- [[CURRENT_STATE]]
- [[CURRENT_TASK]]
- [[CURRENT_BLOCKERS]]
- [[CURRENT_PRIORITIES]]
- [[builder/CONTEXT_CONTRACT]]
- [[_meta/MEMORY_RULES]]

## Canonical knowledge areas

- Architecture → `architecture/`
- Invariants → `invariants/`
- Confirmed findings → `findings/`
- Decisions → `decisions/`
- Workstreams → `workstreams/`
- Product / roadmap / score → `product/`
- Domain knowledge → `domains/`
- Historical evidence → `history/`

## Current snapshot

- Runtime/data `main` HEAD: `a7c4f03b5fae5804d47c6e1a3d470e903a89d47f`
- Latest `main` commit: `auto: tennis live 22:02` — runtime/data only.
- PR #10: **OPEN**, not merged.
- PR #10 head: `f2f7831fdaead6667b6eb53c0021a7bc0377eebf`
- Exact PR-head CI: **GREEN**, run `31741469276`.
- P0-A: **OPEN** — semantic blockers remain despite green CI.

See [[CURRENT_STATE]] for the current operational truth.
