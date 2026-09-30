---
type: memory-home
tier: warm
status: active
---
# SportsBrainMemory V2

SportsBrainMemory is the versioned Knowledge Operating System for SportsBrain.

Start with [[00_HOME]] for the two-minute operational view, then read
[[architecture/OPERATIONAL_KNOWLEDGE_BASE]] for the source-of-truth policy and
the role-bounded navigation map. The current operational snapshot is
[[CURRENT_STATE]]; it is intentionally refreshed from current source/PR
evidence and must never be used to rewrite historical records.

Installation and bootstrap references: [[BOOTSTRAP]], [[CLAUDE]], and
[[SETUP]].

The authoritative vault is `/Users/philiprassillier/SportsBrain-Memory`.
The Obsidian mirror is `/Users/philiprassillier/Downloads/SportsBrain-Memory`.
Canonical Git state wins on divergence; use [[SETUP]] for the one-way sync,
conflict handling, and mirror-freshness contract.

- **Human UI:** Obsidian, starting at [[00_HOME]], with near-live status at [[_live/LIVE_STATUS]].
- **Persistence:** private Git repository for canonical Memory; `_live/` is generated operational state.
- **Canonical truth:** first-class records; generated views never own volatile truth.
- **AI context:** task-bounded V1 context packets, deterministic Context Compiler V3 packs, Builder Bootstrap V4 packages, and read-only Dispatcher Context Envelope V1 delivery in external artifacts.
- **Consistency audit:** read-only Memory Consistency / Governance Auditor V5 reports deterministic governance, authority, Builder-state, dependency, safety, and external-output findings.
- **Drift planning:** read-only Drift Resolution Planner V7 turns V5 findings and optional V6 envelope evidence into deterministic, human-review remediation proposals.
- **Governance:** CODEX is the sole SportsBrain builder platform. Current bootstrap governance supports Builders 1–5; Builder 5 owns Autonomous Development / Night Shift Dispatcher orchestration, and the CEO is the final gatekeeper.

Run `python tools/memory.py acceptance` before trusting a migrated/installed Memory. Build an on-demand V3 pack with `python tools/memory.py context build --consumer builder-4 --task "continue provider cascade" --budget-tokens 6000`, or request a Builder Bootstrap V4 package with `python tools/memory.py builder-bootstrap build --builder 5 --task-id TASK-EXAMPLE --task "request dispatcher bootstrap context" --json`. Run `python tools/sync_memory.py --help` for safe live synchronization.

Run `python tools/memory.py audit-consistency --json` for a read-only V5 audit; add `--vault /path/to/external-vault` to inspect runtime projections. Builder Bootstrap and audit artifacts never launch agents, grant authorization, or modify canonical Memory.

Build a deterministic worker context envelope over V3/V4/V5 with `python tools/memory.py dispatcher-context-envelope build --builder 1 --task-id TASK-EXAMPLE --task "request bounded context" --json`. Worker targets are Builders 1–4; Builder 5 owns dispatcher orchestration and is not a worker target. The envelope is read-only, fails closed on mandatory governance/dependency/safety problems, keeps all authorization fields `NOT_PROVIDED`, and writes only when an explicit external `--output` is supplied.

Build or validate an external V7 drift plan with `python tools/memory.py drift-resolution-plan build --reference-time 2026-09-16T12:00:00Z` and `python tools/memory.py drift-resolution-plan validate /external/DRIFT_RESOLUTION_PLAN.json`. The planner is read-only: remediation entries are proposals, canonical history and runtime projections are unchanged, and no Dispatcher or Builder is launched.
