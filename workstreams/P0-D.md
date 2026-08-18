---
id: WS-P0-D
type: "workstream"
tier: "warm"
status: "active"
workstream: "P0-D"
last_updated: "2026-08-18T00:00:00+02:00"
freshness_class: "release-bound"
---
# P0-D — Governance & Data Integrity

## Objective

Bound every writer, separate hard safety policy from tuning, govern model/Tennis rollout and make historical data migrations auditable.

## Packets

- D1 AI healer source mutation removal
- D2 Writer registry / bot persistence primitive
- D3 Hard policy vs strategy config
- D4 Tennis rollout evidence registry
- D5 Historical identity + migration manifests
- D6 Runtime-data architecture ADR / source-release provenance

## Known findings

- FND-20260814-015 through FND-20260814-018
- FND-20260814-023.

## Dependency

Do not start while P0-A remains open.


## V1 readiness note

Writer/governance implementation is prebuilt and split by authority class.
