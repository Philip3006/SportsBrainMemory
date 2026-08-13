---
type: "architecture"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Execution Planes & Release Provenance

## Execution planes

SportsBrain runs across:
- GitHub Actions
- local macOS launchd
- Cloudflare Worker/KV
- manual/Builder operations.

Jobs are not all simple fixed intervals. They include:
- fixed interval
- cron set
- windowed interval
- event-driven with fallback
- manual/recovery.

## Release truth

`main` HEAD can be a runtime/data bot commit.

Therefore future publication/monitoring must distinguish:
- `source_release_sha`
- `runtime_data_sha`
- `worker_release_sha`
- PWA/public build provenance.

## Current known monitoring mismatch

Current health assumptions already drift from real workflow schedules and can represent failed jobs as `ok`.

See [[workstreams/P0-B]] and [[domains/MONITORING_AND_RECOVERY]].
