---
type: "workstream"
tier: "warm"
status: "planned_blocked"
workstream: "P0-C"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# P0-C — Privacy & Persistence

## Objective

Separate public sports/product data from authenticated private user financial/betting state without PWA downtime.

## Phases

1. Inventory/freeze private publication surfaces.
2. Clean public product schema.
3. Authenticated private `/me` state with strict user isolation.
4. PWA dual-fetch migration.
5. Stop static private publication.
6. Migrate canonical private ledger to a private durable store.
7. Reconcile and cut over.
8. Remove active-tree private artifacts.
9. Historical cleanup only as separate explicit migration.

## Target datastore

Mature target preference: transactional private database. A separate private Git data repo is acceptable only as a staged bridge if explicitly temporary.

## Known findings

- FND-20260814-011 through FND-20260814-014.

## Dependency

Implement after P0-A and with P0-B truth monitoring in place for migration safety.
