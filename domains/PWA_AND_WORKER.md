---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# PWA & Cloudflare Worker

## PWA

Static GitHub Pages frontend uses public/static JSON plus Worker data. Historical UI contained multiple actionability paths; P0-A is consolidating Value semantics.

## Worker

Responsibilities include:
- signals snapshots
- per-user routing/tokens
- pending bet queue
- cancellation queue
- push subscriptions
- workflow/recovery dispatch.

## P0-A target

Worker resolves canonical signal server-side, derives trusted risk state, validates 5%/max-three/current odds/freshness and stores canonical identity rather than trusting client semantics.

## Privacy target

Public product data and private `/me` user state must be separate. Missing private snapshot must never fall back to another/default user's private data.
