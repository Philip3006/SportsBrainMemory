---
id: RUNBOOK-AUTOMATIC-MEMORY-SYNC
type: runbook
tier: warm
status: active
canonical: true
graph_domain: memory
graph_role: operational
last_updated: 2026-10-01T00:00:00Z
freshness_class: stable
---
# Automatic SportsBrain → Memory → Obsidian

Related: [[_meta/SOURCE_HIERARCHY]], [[_meta/MEMORY_RULES]],
[[runbooks/INDEX]], [[architecture/OPERATIONAL_KNOWLEDGE_BASE]].

## Trigger / evidence boundary

Public SportsBrain `origin/main` is polled by Memory's
`.github/workflows/sportsbrain-source-sync.yml` every ten minutes (best effort,
not a delivery SLA), or by workflow_dispatch. Full history is fetched with no
SportsBrain write token. Only Git identities, path counts and squash-subject PR
links are ingested; free-form commit text and runtime/private payloads are not.

`tools/sync_from_sportsbrain.py` uses existing V2 events, canonical current-state
record ownership, manifest and renderer. A meaningful release is the newest
first-parent commit with changes outside `data/`, `docs/data/`, `results/`,
`logs/`. This deliberately conservative rule does not treat artifact-only
changes as architecture releases. The source-release marker is corroborated
against Git ancestry and recorded separately; a lagging marker cannot conceal
newer source. Runtime/data head is the inspected main SHA, not deployment proof.

Same inspected head/release returns NO_OP without file writes or a new commit.
All content and event identities derive from Git evidence, not cron execution
time. `last_successful_import` identifies the imported Git SHA; evidence_timestamp
is its commit timestamp, not a fabricated runtime capture time. Historical
manual narratives and CEO findings are retained and never auto-closed.

## Check / action

Import is staged in an isolated copy. Unit tests, strict/operational/graph/
visual validators and acceptance gates must pass before files are copied back.
Failed imports retain last-good canonical state. Status is emitted to the
workflow artifact; canonical last-success status is `_meta/source_sync_status.json`.

One stable branch `automation/sportsbrain-source-sync` and at most one open PR
are used. Existing commits must be automation-owned and the entire diff must
remain in the explicit importer allowlist. Unexpected code, policy, finding,
decision, deletion or manual commit blocks auto-merge. Main is merged normally,
never rebased or force-pushed. Existing generated graph/context views are
refreshed by the canonical renderer; the runtime Semantic Graph V2 is rebuilt
and validated after local Vault sync, outside the canonical checkout.

GitHub requires Actions read/write permissions, permission for Actions to create
PRs, repository auto-merge enabled, and main branch protection requiring the
Memory validation `validate` check. The workflow deliberately refuses automatic
merge without these settings. GITHUB_TOKEN-created PR runs can require human
approval, so validation is explicitly dispatched at the automation branch.
Only Memory's GITHUB_TOKEN is used; no PAT/cross-repository secret is required.

At implementation audit: auto-merge was disabled and main unprotected. These
settings must be reviewed/enabled separately; this PR does not change them.

## Local post-merge activation (not performed by this PR)

Canonical clone: `/Users/philiprassillier/SportsBrain-Memory` (main).
Vault: `/Users/philiprassillier/Downloads/SportsBrain-Memory`.
Source checkout: `/Users/philiprassillier/sportsbrain` (read-only inspection).

After review/merge and resolving any manifest conflicts:

```sh
python3 /Users/philiprassillier/SportsBrain-Memory/tools/install_memory_sync_launchagent.py
python3 /Users/philiprassillier/SportsBrain-Memory/tools/install_memory_sync_launchagent.py --status
```

The installer writes only the user job
`~/Library/LaunchAgents/com.sportsbrain.memory-sync.plist`, uses bootstrap and
kickstart without sudo, runs at load and every 300 seconds, and retains the
existing single-instance file lock. Logs are under `~/Library/Logs/SportsBrain/`.
The generated plist uses the verified interpreter and script paths. Reinstall is
idempotent. `--uninstall` unloads/removes that exact job; knowledge is retained.

## Abort / recovery / rollback

- **SYNC_BLOCKED / clone edits:** inspect status, preserve edits, reconcile
  manually. Do not discard or reset work. Sync checks edits before fetching.
- **Divergence:** reconcile reviewed commits normally; no destructive reset.
- **Vault conflict:** review reported exact paths, keep personal edits in
  noncanonical notes or reconcile explicitly. New-name collisions also block.
  Missing manifest requires explicit recoverable seed, never automatic seeding.
- **Graph failure:** status DEGRADED; last-good runtime graph remains intact.
  Correct the source/validation error and rerun sync.
- **Workflow failure:** inspect sanitized status artifact and validation logs.
  Failed workflow does not update main. Check permissions/settings above.
- **Agent not loaded:** inspect `--status`, paths and user session; rerun the
  installer only after approval. No system daemon is used.

Offline/asleep Macs simply retain their last Vault state. Remote automation may
continue. After wake/network availability the next user-agent run fast-forwards
Memory main, syncs tracked knowledge and regenerates the graph. `.obsidian/`,
personal-only files and unsafe local edits are never silently overwritten.

Save: source status artifact, exact Memory/source SHAs, validation outcome,
conflict paths and LaunchAgent loaded status. Never save credentials or ledger
payloads. Rollback automation by disabling its workflow/job, not by erasing notes.
