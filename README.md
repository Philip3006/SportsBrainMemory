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
- **AI context:** task-bounded V1 context packets, deterministic Context Compiler V3 packs, Builder Bootstrap V4 packages, and read-only Dispatcher Context Envelope V1 delivery in external artifacts.
- **Consistency audit:** read-only Memory Consistency / Governance Auditor V5 reports deterministic governance, authority, Builder-state, dependency, safety, and external-output findings.
- **Governance:** CODEX is the sole SportsBrain builder platform. Current bootstrap governance supports Builders 1–5; Builder 5 owns Autonomous Development / Night Shift Dispatcher orchestration, and the CEO is the final gatekeeper.

Run `python tools/memory.py acceptance` before trusting a migrated/installed Memory. Build an on-demand V3 pack with `python tools/memory.py context build --consumer builder-4 --task "continue provider cascade" --budget-tokens 6000`, or request a Builder Bootstrap V4 package with `python tools/memory.py builder-bootstrap build --builder 5 --task-id TASK-EXAMPLE --task "request dispatcher bootstrap context" --json`. Run `python tools/sync_memory.py --help` for safe live synchronization.

Run `python tools/memory.py audit-consistency --json` for a read-only V5 audit; add `--vault /path/to/external-vault` to inspect runtime projections. Builder Bootstrap and audit artifacts never launch agents, grant authorization, or modify canonical Memory.

Build a deterministic worker context envelope over V3/V4/V5 with `python tools/memory.py dispatcher-context-envelope build --builder 1 --task-id TASK-EXAMPLE --task "request bounded context" --json`. Worker targets are Builders 1–4; Builder 5 owns dispatcher orchestration and is not a worker target. The envelope is read-only, fails closed on mandatory governance/dependency/safety problems, keeps all authorization fields `NOT_PROVIDED`, and writes only when an explicit external `--output` is supplied.
