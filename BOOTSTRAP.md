---
type: bootstrap
tier: hot
status: active
---
# SportsBrainMemory V1 Bootstrap

1. Read [[00_HOME]].
2. Read [[CURRENT_STATE]] and [[CURRENT_TASK]].
3. If CURRENT_TASK is NONE, Builder MUST STOP.
4. For an approved task, compile its context with `python tools/memory.py context TASK-ID`.
5. External current source/runtime evidence outranks stale Memory.
6. Generated views are projections; never edit them as canonical truth.
7. No secrets or credentials belong in Memory.
