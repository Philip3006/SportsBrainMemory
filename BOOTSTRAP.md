---
type: bootstrap
tier: hot
status: active
---
# SportsBrainMemory V2 Bootstrap

1. Read [[00_HOME]].
2. Read [[CURRENT_STATE]] and [[CURRENT_TASK]].
3. If CURRENT_TASK is NONE, Builder MUST STOP.
4. For an approved task, load the role packet under `builder/context/`; compile a task packet only with `python tools/memory.py context TASK-ID`.
5. External current source/runtime evidence outranks stale Memory.
6. Generated views are projections; never edit them as canonical truth.
7. No secrets or credentials belong in Memory.
8. Canonical Memory and `_live/` operational status are separate; runtime-only status is never canonical by default.
9. CODEX is the sole builder platform. Historical Claude documents are not active instructions.
