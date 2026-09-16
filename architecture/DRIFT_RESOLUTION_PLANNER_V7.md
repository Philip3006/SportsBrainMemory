# Memory Drift Resolution Planner V7

The Drift Resolution Planner V7 is a read-only review layer over the Memory
Consistency / Governance Auditor V5 and the Dispatcher Context Envelope V1.
It converts already observed drift into deterministic remediation proposals for
human review. It does not repair, promote, authorize, launch, merge, deploy,
activate, or rewrite anything.

## Evidence contract

The planner consumes the V5 audit as its primary source and may consume an
external V6 envelope. The V5 audit digest is re-derived during validation. A
V6 envelope with a different source Memory SHA is preserved and flagged as
stale; it is never silently treated as current. Missing, conflicting, stale,
unknown, or failed-closed context remains visible in the plan.

Each remediation record retains the finding identity, status, domain, severity,
affected entities, canonical/current-view paths, runtime paths, authority
classes, Dispatcher impact, proposed remediation class, prerequisite evidence,
CEO decision state, fail-closed reason, provenance, and a per-record digest.

Remediation classes are:

- `NO_ACTION`
- `REFRESH_CURRENT_VIEW`
- `REGENERATE_DERIVED_VIEW`
- `REVIEW_CANONICAL_CONFLICT`
- `PROMOTION_REVIEW_REQUIRED`
- `REMOVE_UNSUPPORTED_RUNTIME_REFERENCE`
- `GOVERNANCE_REVIEW_REQUIRED`
- `SAFETY_REVIEW_REQUIRED`
- `INSUFFICIENT_EVIDENCE`

`CONTEXT_BLOCKING`, `CONTEXT_DEGRADED`, and `NON_BLOCKING` describe impact on
future Dispatcher context only. They do not make an execution decision.

## Safety boundary

Plans are noncanonical external artifacts. The explicit output writer rejects
paths inside canonical Memory and the external Vault, writes JSON and Markdown
atomically, and validates the JSON after writing. No generated plan is stored
under canonical `events/records`, `_live`, or the Vault by default.

Every plan keeps these boundaries visible:

- `NO-BET`
- `NO-LIVE-ACTIVATION`
- `SEALED 2425/2526`
- `Closing odds benchmark-only`

All remediation actions are proposals only. Automatic repair, candidate
promotion, and authorization remain false.

## CLI

Build an in-memory Markdown plan:

```sh
python3 tools/memory.py drift-resolution-plan build \
  --reference-time 2026-09-16T12:00:00Z
```

Build and write only to an explicitly supplied external directory or JSON file:

```sh
python3 tools/memory.py drift-resolution-plan build \
  --envelope /external/DISPATCHER_CONTEXT_ENVELOPE.json \
  --vault /external/ObsidianVault \
  --output /private/tmp/sportsbrain-drift-plan \
  --reference-time 2026-09-16T12:00:00Z \
  --json
```

Validate or inspect an external plan:

```sh
python3 tools/memory.py drift-resolution-plan validate /external/DRIFT_RESOLUTION_PLAN.json
python3 tools/memory.py drift-resolution-plan inspect /external/DRIFT_RESOLUTION_PLAN.json
```

This layer is intentionally ready to serve a future Dispatcher request of
`builder + task metadata -> validated bootstrap/context evidence`, but it does
not implement a Dispatcher or decide whether a task is safe to execute.
