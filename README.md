---
type: memory-home
tier: warm
status: active
---
# SportsBrainMemory V2

SportsBrainMemory is the versioned Knowledge Operating System for SportsBrain.

- **Human UI:** Obsidian, starting at [[00_HOME]], with near-live status at [[_live/LIVE_STATUS]].
- **Persistence:** private Git repository for canonical Memory; `_live/` is generated operational state.
- **Canonical truth:** first-class records; generated views never own volatile truth.
- **AI context:** task-bounded V1 context packets and deterministic Context Compiler V3 packs in Vault `_live/context/`.
- **Governance:** CODEX is the sole SportsBrain builder platform. Current governance supports Builder 1 / Builder 2 / Builder 3 / Builder 4, and the CEO is the final gatekeeper.

Run `python tools/memory.py acceptance` before trusting a migrated/installed Memory. Build an on-demand pack with `python tools/memory.py context build --consumer builder-4 --task "continue provider cascade" --budget-tokens 6000`. Run `python tools/sync_memory.py --help` for safe live synchronization.
