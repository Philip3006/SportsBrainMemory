---
type: "meta-protocol"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# Update Protocol

After each CEO audit:

1. Verify current source/runtime/PR state.
2. Create or update confirmed Findings.
3. Update affected invariant status/evidence.
4. Update `CURRENT_STATE.md`.
5. Update `CURRENT_BLOCKERS.md`.
6. Update `CURRENT_TASK.md` when active scope changed.
7. Rebuild `builder/CURRENT_CONTEXT_PACKET.md`.
8. Archive/supersede obsolete task packet if needed.
9. Update historical audit index.
10. Change Production Score only with production evidence.
11. Run `python tools/validate_memory.py`.

ChatGPT may generate an update bundle. `tools/apply_update.py` applies it locally only; it never pushes Git.
