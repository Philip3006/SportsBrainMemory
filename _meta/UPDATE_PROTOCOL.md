---
type: "meta-protocol"
tier: "warm"
status: "active"
last_updated: "2026-09-13T23:34:53+02:00"
freshness_class: "stable"
---
# Update Protocol — V2

For a canonical V2 change, use the structured event contract:

1. classify the source change as canonical or runtime-only;
2. write a verified event to `events/records/` (or pending evidence to `events/pending/`); builder events must include a matching `builder_number`;
3. update only the canonical owner record;
4. render projections and bounded role packets;
5. run the V2 validator and acceptance suite;
6. create a coherent Memory-only Git commit for CEO review.

Runtime-only bot updates belong in `_live/` and do not create a canonical
event or commit.

Every builder completion handoff must start with exactly one of `BUILDER: 1`,
`BUILDER: 2`, or `BUILDER: 3`. Handoffs without this identity are incomplete
and cannot be accepted by the CEO gate.

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
