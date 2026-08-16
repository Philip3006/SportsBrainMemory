---
id: EVD-P0B-001-PROD-001
type: evidence
title: P0-B1 Execution Truth production closure evidence
status: current
canonical: true
tier: warm
created_at: 2026-08-16T23:00:00+02:00
updated_at: 2026-08-16T23:00:00+02:00
freshness_class: release-bound
evidence_type: production-source
sha: 5dc8ff7dd7434420ad856187fdde74d98dc04dbc
environment: production
scope: P0-B1 Execution Truth — fail-closed exit evidence at health writer boundary
workstream: P0-B
verified_by:
  - VER-P0B-001-PROD-001
findings:
  - FND-20260814-005
---
# P0-B1 Execution Truth — Production Closure Evidence

## Source release

- Source release SHA: `5dc8ff7dd7434420ad856187fdde74d98dc04dbc`
- PR #11, approved head: `9ff8e8da739dc2508da3989bb668234a2ad9e74a`
- Post-merge CI run: `31970751973` — **success**

## Publication

- Publication commit: `769c26f06bfbb8a8544116d76f4fd2b91b9da8d0`
- Publication scope: `docs/data/health.json` only
- GitHub Pages publication verified green by Builder/CEO verification chain.

## Production semantics verified

- MON-001 contradiction count = 0 in verified published channels: no `ok`/`degraded` + nonzero exit contradiction observed in production.
- `tennis_scan` exit=1 → error (not ok/degraded).
- `tennis_settle` exit=1 → error.
- `tennis_closing_odds` exit=1 → error.
- `tennis_retrain` exit=1 → error.
- `bundesliga2_settle` may remain stale; execution failure is visible via MON-001 evidence.
- Valid exit_code=0 ok/degraded states remain valid.
- `signals_data_fresh` and `live_scores_fresh` intentionally use `exit_code=null` as freshness pseudo-jobs.
- `source_release_sha` and `runtime_data_head` remain separate in published health.

## OPS-006 scope note

OPS-006 (full execution-plane provenance) remains future scope and is **not** marked fully closed by this evidence.
