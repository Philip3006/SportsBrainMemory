---
id: WS-MEMORY-V2
type: workstream
tier: warm
status: active
workstream: MEMORY-V2
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: stable
---
# Memory V2 — Live Obsidian System

Builder C owns the canonical/lived-layer separation, event model, update
engine, validators, role packets, and safe user-level Obsidian sync.

Release state: implementation complete on `feat/memory-v2-live-obsidian`,
pending CEO review. The formal live sync is installed only as a user-level
LaunchAgent and never touches system-wide launchd jobs.
