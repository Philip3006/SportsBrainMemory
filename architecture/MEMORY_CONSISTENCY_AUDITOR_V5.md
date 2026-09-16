# Memory Consistency / Governance Auditor V5

The Consistency Auditor V5 is a read-only, deterministic audit over current
Memory governance and explicitly supplied external runtime projections. It
does not compile or promote context, launch Builders or a dispatcher, authorize
execution, merge, deploy, change canonical records, or mutate the Vault.

## Audit scope

The audit compares the governed Builder 1–5 roster and exact role baselines
across the governance module, Context Compiler V3 consumers/profiles, Source
Observer handoff validation, Semantic Graph V2 identity seeding, Builder
Bootstrap V4 validation, and current architecture claims. Builder 6 and later
numbers fail closed until an explicit governance update extends the roster.
Builder 5 is **Autonomous Development / Night Shift Dispatcher Owner**. Its
partner set (Builders 1–4) is visibility context only and grants no merge,
deploy, activation, provider-call, or CEO-decision authority.

When a Vault is supplied, the audit reads `_live/SOURCE_OBSERVER.json`,
`SOURCE_CANDIDATES.json`, `BUILDER_HANDOFFS.json`, `BLOCKERS.json`,
`_live/context`, `_live/builder-bootstrap`, and `_live/graph`. Runtime evidence
is retained as candidate or runtime-derived evidence. Missing handoffs are
reported as UNKNOWN; AGING and STALE evidence remain visible, and state
conflicts are not auto-resolved.

The auditor checks authoritative dependency satisfaction, candidate promotion
flags, canonical/verified disagreement, branch/head/PR/blocker/status/role
projection drift, circular or unsupported dependencies, stale/unknown current
state, mandatory NO-BET/no-live/sealed safety invariants, and resolved output
paths. A missing mandatory safety invariant or an artifact claiming execution
or CEO authority is an error and fails closed.

## Finding contract

The JSON report is deterministic for a fixed source SHA, reference time, and
runtime input. Findings are ordered by severity, domain, status, and stable
finding ID. Each finding includes `finding_id`, `severity`, `domain`, `status`,
`summary`, `affected_entities`, `evidence`, `authority_classes`,
`source_paths`, and `recommended_human_action`. Statuses are
`CONSISTENT`, `WARNING`, `STALE`, `UNKNOWN`, `NONAUTHORITATIVE_ONLY`,
`CONFLICT`, `GOVERNANCE_DRIFT`, `SAFETY_INVARIANT_MISSING`, and
`FAILED_CLOSED`.

## CLI

```text
python3 tools/memory.py audit-consistency
python3 tools/memory.py audit-consistency --json --reference-time 2026-09-16T12:00:00Z
python3 tools/memory.py audit-consistency --vault /path/to/external-vault --output /private/tmp/memory-audit
```

The command performs no writes unless `--output` is explicitly supplied. The
requested report path must resolve outside both the canonical Memory checkout
and the external Vault runtime root. Report generation is a diagnostic result;
it never authorizes a future dispatcher task.

## Safety boundary

NO-BET, no-live-activation, and SEALED 2425/2526 remain mandatory. Closing
odds remain a benchmark/CLV artifact. Runtime candidates remain
`canonical=false` and `promotion_required=true`; no artifact produced by this
layer grants CEO or execution authorization. No LaunchAgent cadence or
production/runtime/Cloudflare/ledger/research data is changed.
