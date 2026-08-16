---
id: CMP-BETTING
type: component
title: Canonical betting flow
status: active
canonical: true
tier: warm
source_paths:
  - scripts/consume_pending_bets.py
  - src/betting/
  - cloudflare/worker.js
---
# Canonical Betting Flow

PWA → Worker → pending queue → Consumer → durable ledger, governed by P0-A invariants.
