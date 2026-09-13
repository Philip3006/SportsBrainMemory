---
type: "builder-entry"
tier: "hot"
status: "active"
freshness_class: "stable"
---
# CODEX Builder — Start Here

For a normal SportsBrain Builder session:

1. Read the role packet under `builder/context/` and then `builder/CURRENT_CONTEXT_PACKET.md`.
2. Verify its Task ID matches `CURRENT_TASK.md`.
3. Inspect only the SportsBrain source files/direct callers/tests required by that task.
4. Execute the task.
5. Do not merge unless later explicitly approved.

Minimal instruction from the owner can be:

> Read the SportsBrain shared-memory current context packet and execute CURRENT_TASK. Load only referenced context. Do not merge.

If the packet is stale or task ID differs, regenerate it with:

`python tools/build_context.py`

Then validate:

`python tools/validate_memory.py`

CODEX is the sole builder platform. Builder 1/2/3 are numbered ownership
roles, not permission to merge or bypass the CEO gate.
