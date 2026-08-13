---
type: "architecture"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Data & Persistence Architecture

## Key authorities

- Refreshed odds → `data/cache/odds_state.json`
- Tennis lifecycle → `data/cache/tennis_event_states.json`
- Tennis fixture continuity → Tennis fixture registry
- Financial history → per-user ledger (current architecture; privacy migration planned)
- Pending/cancel intents → Cloudflare KV queues
- Published product snapshot → generated signals/public JSON + Worker KV replicas

## Hard persistence principle

> A local write or local Git commit is not sufficient proof of canonical durable persistence.

For money-affecting queue items:
- validate/classify intent;
- persist accepted mutation durably;
- verify durable canonical state;
- then ACK queue;
- retry safely after infrastructure failure.

## Current transition

P0-A is hardening current Git-backed ledger persistence.
P0-C will separate public product data from private user state and define the long-term private financial datastore.

## Privacy constraint

The Memory stores architecture and findings about private data, never the private ledger rows themselves.
