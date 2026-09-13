---
type: "setup-guide"
tier: "warm"
status: "active"
last_updated: "2026-09-13T23:04:08+02:00"
freshness_class: "stable"
---
# SportsBrain Shared Memory V2 — Setup

## 1. Keep it private

Create a **separate private Git repository** for this folder, e.g. `SportsBrain-Memory`.

Do not put this Memory in the public SportsBrain source repo.

The Memory contains no intended secrets/private ledger rows, but it still contains internal architecture, incidents and security findings and should remain private.

## 2. Canonical vs near-live layers

Canonical reviewed records live in the private Git repository. Obsidian is the
human UI. The generated `_live/` layer contains source/runtime/CI/provider/sync
observations and must not be treated as canonical history.

No community plugins are required. Open the actual Vault once; the user-level
sync service below updates files without requiring an Obsidian restart.

## 3. CODEX builders

Keep a local clone next to the SportsBrain code checkout, for example:

```text
projects/
  sportsbrain/
  SportsBrain-Memory/
```

Give CODEX access to the Memory directory and direct it to read:

`SportsBrain-Memory/builder/CURRENT_CONTEXT_PACKET.md`

Normal Builder instruction can be as small as:

```text
Read the SportsBrain shared-memory current context packet and execute CURRENT_TASK.
Inspect only the referenced context and required source files.
Do not merge.
```

Do not ask CODEX to recursively read the entire Memory. Use the numbered,
role-bounded packet for Builder 1, 2, 3, or CEO.

Before a Builder run, regenerate the packet:

```bash
python SportsBrain-Memory/tools/build_context.py
python SportsBrain-Memory/tools/validate_memory.py
```

## 4. ChatGPT / CEO decision ingestion

Long-term shared access:
1. push this Memory to a private GitHub repository;
2. grant the connected GitHub integration access to that repository;
3. ChatGPT/CEO reads it read-only.

The CEO still checks current SportsBrain source/runtime before treating Memory as current truth.

CEO-approved events use this payload shape:

```json
{
  "events": [{
    "event_id": "EVT-YYYYMMDD-NNN",
    "timestamp": "2026-09-13T23:00:00+02:00",
    "type": "CEO_DECISION",
    "domain": "example",
    "summary": "Decision text",
    "source_repository": "ChatGPT CEO brief",
    "builder": "CEO",
    "builder_number": "CEO",
    "ceo_gate_state": "approved",
    "affected_workstreams": [], "findings": [], "invariants": [],
    "supersedes": [], "evidence": ["CEO approval reference"],
    "verification_state": "ceo_approved",
    "canonical": true
  }]
}
```

Apply it with `python tools/update_memory.py payload.json`. The engine is
idempotent, validates before an optional Memory-only commit, and rejects
secrets, duplicate IDs with changed payloads, invalid timestamps, and unsafe
paths. A builder report uses `verification_state: builder_report` and is held
under `events/pending/` until CEO or independent verification promotes it.

## 5. Updating without an approved event

Legacy bundles remain supported with:

```bash
python SportsBrain-Memory/tools/apply_update.py memory-update.json
```

The V2 updater may modify only the Memory tree, renders generated views and
packets, validates, rolls back on failure, and performs no push.

## 6. Live sync and recovery

The recommended cadence is 90 seconds through a user-level macOS LaunchAgent
(`gui/501`, no sudo). Each run fetches the configured branch, refuses dirty
Memory worktrees, pulls only by fast-forward, checks the Vault manifest, and
stops on local edits or divergence. It never hard-resets or discards files.
When canonical packet names are intentionally replaced, sync may remove only
the three unchanged retired generated packet paths explicitly listed in the
sync manifest; every other missing or modified Vault file is preserved and
causes a visible conflict.

The initial seed creates a recoverable `.memory-backups/pre-v2-*` snapshot in
the Vault. After seeding, edit conflicts are reported in
`_live/SYNC_STATUS.md` and the job resumes only after the user resolves the
conflict. Disable with `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.sportsbrain.memory-v2.plist`;
re-enable with `launchctl bootstrap gui/$(id -u) ...plist`.

If Memory is older than six hours behind the latest meaningful source change,
it is `AGING`; after 24 hours it is `STALE`. Runtime status can independently
be `ONLINE`, `DEGRADED`, `STALE`, or `SYNC BLOCKED`.

## 7. V1 compatibility

The V1 Markdown/context-packet workflow remains the canonical compatibility
layer. V2 adds structured local event validation; it does not require MCP or a
community Obsidian plugin.

## 8. Daily usage

You can simply tell ChatGPT:
- “SportsBrain weiter”
- “Wo stehen wir?”
- paste a Builder handoff; it remains pending evidence until verified.

The CEO maps new findings into the Memory/task system and produces the next bounded Builder packet.
