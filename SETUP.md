---
type: "setup-guide"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# SportsBrain Shared Memory — Setup

## 1. Keep it private

Create a **separate private Git repository** for this folder, e.g. `SportsBrain-Memory`.

Do not put this Memory in the public SportsBrain source repo.

The Memory contains no intended secrets/private ledger rows, but it still contains internal architecture, incidents and security findings and should remain private.

## 2. Obsidian

Open the local `SportsBrain-Memory/` directory as an Obsidian Vault.

No community plugins are required. Git is the canonical sync/version layer in V1.

## 3. Claude Code

Keep a local clone next to the SportsBrain code checkout, for example:

```text
projects/
  sportsbrain/
  SportsBrain-Memory/
```

Give Claude Code access to the Memory directory using its additional-directory mechanism, then direct it to read:

`SportsBrain-Memory/builder/CURRENT_CONTEXT_PACKET.md`

Normal Builder instruction can be as small as:

```text
Read the SportsBrain shared-memory current context packet and execute CURRENT_TASK.
Inspect only the referenced context and required source files.
Do not merge.
```

Do not tell Claude to recursively read the entire Memory.

Before a Builder run, regenerate the packet:

```bash
python SportsBrain-Memory/tools/build_context.py
python SportsBrain-Memory/tools/validate_memory.py
```

## 4. ChatGPT / CEO

Long-term shared access:
1. push this Memory to a private GitHub repository;
2. grant the connected GitHub integration access to that repository;
3. ChatGPT/CEO reads it read-only.

The CEO still checks current SportsBrain source/runtime before treating Memory as current truth.

## 5. Updating without Claude

ChatGPT can generate a small JSON update bundle.
Apply it locally with:

```bash
python SportsBrain-Memory/tools/apply_update.py memory-update.json
```

The updater:
- may modify only the Memory tree;
- runs validation;
- rolls back local file changes if validation fails;
- performs no Git commit/push.

You then review and version the Memory normally.

## 6. V1 deliberately has no MCP

Do not add MCP, embeddings or semantic retrieval until the file/context-packet workflow becomes an actual bottleneck.

## 7. Daily usage

You can simply tell ChatGPT:
- “SportsBrain weiter”
- “Wo stehen wir?”
- paste Claude’s Builder report.

The CEO maps new findings into the Memory/task system and produces the next bounded Builder packet.
