---
type: "builder-entry"
tier: "hot"
status: "active"
freshness_class: "stable"
---
# CODEX Builder — Start Here

For a normal SportsBrain Builder session:

1. Read [[00_HOME]] and [[architecture/OPERATIONAL_KNOWLEDGE_BASE]].
2. Read the role packet under `builder/context/` and then
   `builder/CURRENT_CONTEXT_PACKET.md`.
3. Verify its Task ID matches `CURRENT_TASK.md`.
4. Inspect only the SportsBrain source files/direct callers/tests required by
   that task, and distinguish merged main from branch-only evidence.
5. Execute the task.
6. Do not merge unless later explicitly approved.

Minimal instruction from the owner can be:

> Read the SportsBrain shared-memory current context packet and execute CURRENT_TASK. Load only referenced context. Do not merge.

If the packet is stale or task ID differs, regenerate it with:

`python tools/build_context.py`

Then validate:

`python tools/validate_memory.py`

CODEX is the sole builder platform. Numbered builder roles are ownership
lanes, not permission to merge or bypass a CEO gate. The current ownership
and dependency view is [[domains/BUILDERS]].
