---
type: "historical-index"
tier: "cold"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "historical"
---
# Incident Timeline

## INC-0001 — Branch contamination by runtime bots

Runtime/launchd writers polluted development branch; branch guards and safe-push hardening followed.

## INC-0002 — PWA fabricated/fallback odds

UI could expose non-market fallback price semantics; later waves hardened fail-closed behavior.

## INC-0003 — False Tennis LIVE

Time/schedule heuristics could imply LIVE without authoritative evidence; Wave 3A/3B introduced TennisEventState/evidence.

## INC-0004 — Absurd EV / stale actionability

Corrupt/stale odds/EV could remain recommendation-like; Waves 0–2 added stronger fail-closed gates.

## INC-0005 — P0-A end-to-end betting safety bypass

PWA/Worker/consumer semantics allowed 5%-cap, source/provenance and current-odds bypasses.

## INC-0006 — P0-A review-loop findings

Multiple green-test revisions still contained orchestration, unit, lifecycle and durability bugs; led to invariant-first review process.

## INC-0007 — Health false-green

Public health showed `status=ok` with failure exit codes, motivating P0-B Monitoring Truth.

## INC-0008 — Public private-state exposure

Public repo/static payloads contain personal financial/betting state, motivating P0-C.
