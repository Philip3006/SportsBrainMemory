# Memory Dispatcher Context Envelope V1 / V6

The Dispatcher Context Envelope is a read-only delivery boundary over the
existing Context Compiler V3, Builder Bootstrap V4, and Consistency Auditor V5
layers. A future Night Shift Dispatcher can submit one governed worker Builder
and task metadata and receive a deterministic, validated context package
without knowing Memory's retrieval internals.

## Governed seam

Worker targets are Builders 1–4. Builder 5 remains
**Autonomous Development / Night Shift Dispatcher Owner** and is the
`MemoryV4BootstrapProvider` / Memory context-provider seam; it is not a worker
target. Builder 6 and later numbers fail closed until a future governance
update explicitly changes the roster.

The envelope consumes V3 for graph traversal and authority-first selection,
V4 for task-specific bootstrap sections, and V5 for read-only consistency
findings. It does not duplicate retrieval or dependency policy, repair
findings, launch a dispatcher, launch an agent, call a provider, spend quota,
merge, deploy, activate production, or make a CEO decision.

## JSON contract

Each envelope includes:

- worker Builder identity and governed role, task identity, repository/path
  scope, declared dependencies, and reference time;
- the relevant V3 context pack and its digest/reference;
- the V4 bootstrap pack and its digest/reference;
- the V5 consistency audit and its digest/reference;
- authoritative dependency states, non-authoritative evidence, blockers,
  contracts, unresolved decisions, stale/conflicting/unknown evidence,
  review flags, provenance, and the exact source Memory SHA;
- immutable authorization fields. Every authorization field is
  `NOT_PROVIDED`; `safety_decision` is `NOT_EVALUATED`;
- a semantic envelope digest that excludes generated time.

The only classifications are `CONTEXT_READY`, `CONTEXT_WARNING`,
`CONTEXT_STALE`, `CONTEXT_CONFLICT`, `CONTEXT_UNKNOWN`, and
`CONTEXT_FAILED_CLOSED`. The envelope never claims that a task is safe,
authorized, approved, deployable, mergeable, or production-ready.

V5 safety-invariant failures, governance drift, source SHA disagreement,
mandatory dependency conflicts, and failed V4 compilation classify the
envelope as `CONTEXT_FAILED_CLOSED`. Stale and unknown evidence remain
visible; no state is silently resolved. Candidate and runtime-derived
evidence remains noncanonical with `canonical=false` and
`promotion_required=true`.

Every valid envelope visibly carries `NO-BET`, `NO-LIVE-ACTIVATION`,
`SEALED 2425/2526`, and `Closing odds benchmark-only`.

## Stable provider interface

The future dispatcher seam is intentionally small:

```text
MemoryV4BootstrapProvider.request(
  builder: 1|2|3|4,
  task_metadata: object,
  repository: string|list,
  allowed_paths: list[string],
  prohibited_paths: list[string],
  declared_dependencies: list[string],
  reference_time: ISO-8601,
  token_budget: integer,
) -> validated DispatcherContextEnvelopeV1
```

The provider may call the CLI or the Python API below. It must treat the
envelope as informational context only and must not infer authorization from
it. The output is JSON plus optional human-readable Markdown; it is
noncanonical and external to both canonical Memory and the Vault runtime.

## CLI

Build without writing:

```text
python3 tools/memory.py dispatcher-context-envelope build \
  --builder 1 \
  --task-id TASK-EXAMPLE \
  --task "Request bounded research context" \
  --repository Philip3006/SportsBrain \
  --allowed-path docs/ \
  --budget-tokens 6000 \
  --json
```

`--vault` is an optional read-only runtime input. Writing requires an explicit
`--output` outside both canonical Memory and the supplied Vault; resolved
symlink-back paths are rejected. Validation and inspection are:

```text
python3 tools/memory.py dispatcher-context-envelope validate /external/ENV.json
python3 tools/memory.py dispatcher-context-envelope inspect /external/ENV.json
```

No scheduler or LaunchAgent configuration is changed. No generated envelope
is written by default.
