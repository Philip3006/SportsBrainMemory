# SportsBrain — Canonical Invariant Registry

**Snapshot:** 2026-08-13, 23:09 Europe/Berlin  
**Production HEAD inspected:** `e1d81da102f8d629e71836c3b8b3d284987fe8b3`  
**P0-A candidate overlay:** `f2f7831fdaead6667b6eb53c0021a7bc0377eebf` — PR #10, **not production**  
**Registry purpose:** Turn CEO rules and system truths into explicit, testable, monitorable contracts.  
**Mutation:** None; generated from read-only inspection.

---

# 1. Status legend

| Status | Meaning |
|---|---|
| ✅ ENFORCED | Strong evidence that the invariant is enforced in current production source at the inspected snapshot. |
| 🟡 PARTIAL | Some enforcement exists, but at least one path/edge/replica remains weak or unverified. |
| 🔴 NOT ENFORCED | Known production path violates or does not enforce the invariant. |
| ⚪ UNVERIFIED | Not enough evidence from this audit to claim either enforced or violated. |
| 🔵 BRANCH CANDIDATE | P0-A candidate appears to implement the invariant, but it is not production and still needs final closure/deployment proof. |
| 🟣 BRANCH PARTIAL | P0-A improves it but a known review blocker/edge remains. |
| — | P0-A does not materially change this invariant. |

**Severity:**
- **P0** — financial safety, data loss, production truth, privacy, or governance boundary that can materially harm correctness/trust.
- **P1** — important reliability/quality invariant; should block higher maturity scores.
- **P2** — desirable hardening/operational quality.

---

# 2. Registry principles

Every hard invariant should eventually have all five:

1. **Canonical owner** — exactly where truth originates.
2. **Enforcement** — where invalid state is blocked.
3. **Deterministic test** — proves the boundary.
4. **Production monitor** — detects violations after deployment.
5. **Failure semantics** — fail closed, degraded, retryable, or permanent reject.

A test without production monitoring is incomplete.
Monitoring without a canonical owner is ambiguous.
A branch implementation without deployed verification is not production enforcement.

---

# 3. Snapshot summary

Total invariants: **159**  
P0 invariants: **63**  
P1 invariants: **96**  
P2 invariants: **0**

Production status at this snapshot:

- ✅ Enforced: **22**
- 🟡 Partial: **65**
- 🔴 Not enforced: **69**
- ⚪ Unverified: **3**

This is not a “defect count”. Some invariants intentionally describe target architecture not yet built. It is a governance map of what must be true before SportsBrain can be rated as a highly trustworthy product.

---

# 4. Master registry

| ID | Domain | Sev | Invariant | Canonical owner | PROD | P0-A overlay | Evidence / current basis | Failure mode | Production monitor | Closure / next action |
|---|---|---:|---|---|---|---|---|---|---|---|
| **BET-001** | Betting | **P0** | Every `source=value` bet must resolve to one real canonical signal by `signal_id`. | Canonical published signal registry | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production Worker accepts client Value payload; P0-A resolves KV signal. | Fabricated/model-unapproved bet enters production ledger. | Value bet without canonical signal; unknown signal_id. | Finish P0-A and verify Worker/public flow. |
| **BET-002** | Betting | **P0** | Canonical signal identity must bind match, market, sport and fixture identity; client may request but not redefine it. | Canonical signal | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production Worker stores client fields; P0-A candidate validates/derives canonical identity. | Valid signal ID authorizes different proposition. | Signal ID ↔ stored identity mismatch. | Finish P0-A; add invariant monitor. |
| **BET-003** | Betting | **P0** | Only exact sources `value` and `manual` are accepted; unknown input must not normalize to `value`. | Bet API contract | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production Worker maps every non-manual source to value. | Unknown source contaminates production population. | Ledger source outside enum; Worker rejected-source metric. | Finish P0-A. |
| **BET-004** | Betting | **P0** | Manual betting must be an explicit user-selected flow; invalid Value requests cannot silently downgrade to manual. | PWA/Worker contract | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Historical paths mixed semantics; P0-A explicitly separates flows. | Model provenance becomes ambiguous. | Value→manual reclassification count must be zero. | Finish P0-A. |
| **BET-005** | Betting | **P0** | All Value actionability surfaces must use the same semantic contract. | Canonical actionability policy | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production `predCard()` computes independent EV>=3 rule. | Different screens disagree whether same proposition is bettable. | Cross-surface actionability parity test. | Finish P0-A; preserve parity tests. |
| **BET-006** | Betting | **P0** | Value actionability requires `signal_status == ACTIVE`. | Signal lifecycle | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Top-rec style gates use status; alternate model-tip paths do not. | Stale/edge-lost signal remains bettable. | Any non-ACTIVE Value button/request. | Finish P0-A. |
| **BET-007** | Betting | **P0** | Value bet must use actual `current_odds`, never scan-time odds presented as current. | Odds-state authority | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production UI contains scan/model-tip paths; P0-A candidate binds current odds. | Ledger entry not equal actionable market price. | Submitted odds != canonical current_odds. | Finish P0-A. |
| **BET-008** | Betting | **P0** | `current_odds` must be finite and >1.0. | Odds-state authority | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Some production gates validate; not universal. | Invalid price generates meaningless risk/EV. | Actionable signal with invalid odds. | Finish canonical contract. |
| **BET-009** | Betting | **P0** | Value odds must be fresh within canonical 30-minute hard window. | Odds-state authority | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Signal status has 30m stale threshold; alternate UI path bypasses. | Stale quote presented as actionable. | ACTIVE with odds age >30m. | Finish P0-A + Wave3D check. |
| **BET-010** | Betting | **P0** | Materially future `odds_ts` must fail closed; limited clock skew only. | Odds-state authority | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production status code lacks universal future guard; P0-A adds bounded skew. | Future timestamp makes stale data look fresh. | Odds timestamp beyond allowed future skew. | Finish P0-A. |
| **BET-011** | Betting | **P0** | Value `current_ev_pct` must be finite, positive and <= canonical MAX_EV (40%). | Canonical gate/config | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Production sidecar corruption guard allows much wider range; P0-A narrows actionability. | Corrupted EV generates unsafe recommendation. | ACTIVE EV <=0, >40%, NaN/Inf. | Finish P0-A and monitor. |
| **BET-012** | Betting | **P0** | Shadow signals are never actionable Value bets. | Signal provenance | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Category/shadow architecture exists; UI provenance historically inconsistent. | Experimental bets enter production. | source=value with shadow flag/tier. | Canonical contract + measurement provenance. |
| **BET-013** | Betting | **P0** | Unsupported signals are never actionable Value bets. | Signal contract | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Not universal on main; P0-A candidate checks. | Unsupported market/data becomes financial action. | Value bet with unsupported flag. | Finish P0-A. |
| **BET-014** | Betting | **P0** | `edge_lost`, stale, no-bet or unrefreshable state must never remain actionable. | Signal lifecycle | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Canonical signal_status supports these; alternate paths bypass. | Known-bad signal remains clickable. | Actionable signal with any disqualifying flag. | Finish P0-A. |
| **BET-015** | Betting | **P0** | Tennis Value signals require explicit canonical event status. | TennisEventState | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production alternate paths do not enforce; P0-A candidate sport-aware. | Unknown lifecycle treated as safe prematch. | Tennis value with missing event_status. | Finish P0-A. |
| **BET-016** | Betting | **P0** | Tennis LIVE/COMPLETED/POSTPONED/CANCELLED/UNKNOWN are non-actionable. | TennisEventState | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Event state exists; global UI/Worker enforcement absent in main. | Bet placed after/while match lifecycle invalid. | Any actionable terminal/live/unknown Tennis signal. | Finish P0-A. |
| **BET-017** | Betting | **P1** | Tennis UPCOMING/AWAITING_START/qualified DELAYED may remain actionable only with fresh canonical odds. | TennisEventState + odds state | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Canonical Tennis states support semantics; P0-A aligns actionability. | Valid delayed match incorrectly blocked or unsafe delayed bet allowed. | Status/odds freshness contradictions. | Parity + trust monitor. |
| **BET-018** | Betting | **P1** | Value odds field may not be arbitrarily edited while preserving canonical `source=value`. | Canonical current odds | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production UI paths permit loosely bound odds; P0-A candidate locks/revalidates. | Recorded price differs from evaluated price. | Submitted value odds != canonical odds. | Finish P0-A. |
| **BET-019** | Betting | **P1** | Deep links, compact cards, match detail and normal cards must not bypass canonical actionability. | PWA action contract | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Multiple production UI paths exist. | Convenience path reopens closed safety hole. | Route-specific actionability parity. | Browser regression suite. |
| **BET-020** | Betting | **P1** | No new Value bet may be created from model-tip/all-odds data without backing canonical signal. | Canonical signal | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production `predCard` builds value from model probability+odds directly. | Informational model view becomes unapproved wager. | Value request without registered signal. | Finish P0-A. |
| **RISK-001** | Risk | **P0** | Final stake must be <= 5% of authoritative current bankroll. | Ledger-derived bankroll / hard CEO invariant | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production Worker cap €25; consumer no bankroll cap. P0-A candidate enforces 5%. | Oversized financial exposure. | Any new stake_pct >5% or recomputed stake>5%. | Finish P0-A + monitor. |
| **RISK-002** | Risk | **P0** | 5% rule applies to both Value and Manual bets. | Hard risk policy | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production manual/value share only absolute cap. | Manual flow bypasses risk policy. | Manual stake >5%. | Finish P0-A. |
| **RISK-003** | Risk | **P0** | Worker must not trust client-supplied bankroll as security authority. | Backend risk state | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production does not authoritative-cap; P0-A uses backend state. | Client spoofs bankroll upward. | Client hint differs; server decision unchanged. | Finish P0-A. |
| **RISK-004** | Risk | **P0** | Consumer independently revalidates bankroll cap from live ledger state. | Ledger | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production consumer writes submitted stake directly. | Worker-only failure reaches ledger. | Consumer accepted >5%. | Finish P0-A. |
| **RISK-005** | Risk | **P0** | Maximum active bets is 3 across every placement boundary. | Hard CEO invariant | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production config says 5; Worker does not enforce 3. | Portfolio exposure exceeds governance. | open+pending >3. | Finish P0-A. |
| **RISK-006** | Risk | **P0** | Worker active-bet count comes from trusted backend state plus pending queue, never client count. | Published risk state + KV pending | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production no canonical max3; P0-A candidate server state. | Client spoofs count. | Server count/client count divergence test. | Finish P0-A. |
| **RISK-007** | Risk | **P0** | If authoritative bankroll/open-bet state is missing or stale, new money actions fail closed. | Backend risk state | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production lacks state gate; P0-A candidate adds freshness. | Unknown risk treated as safe. | Placement with missing/stale risk state. | Finish P0-A. |
| **RISK-008** | Risk | **P1** | Risk-state freshness heartbeat must be independent of expensive scan cadence. | Risk-state publisher | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | P0-A candidate adds heartbeat; final transaction integration still under review. | Healthy system locks betting or uses stale count. | risk published_at age and heartbeat outcome. | Complete final P0-A queue pass. |
| **RISK-009** | Risk | **P0** | Security boundaries reject oversized confirmed stake; they do not silently mutate it after user confirmation. | Worker/consumer | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production has no 5% mutation logic; P0-A candidate reject semantics. | Ledger differs from user-confirmed amount. | Requested stake != stored stake without explicit preconfirm cap. | Finish P0-A. |
| **RISK-010** | Risk | **P1** | `stake_pct` on every new non-zero bet is truthful and recomputable from bankroll-at-placement. | Ledger provenance | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production PWA consumer writes `stake_pct=0.0`. | Risk analytics lies. | stake_pct mismatch recomputation. | Finish P0-A. |
| **QUEUE-001** | Queue | **P0** | Accepted pending bet may be ACKed/deleted only after durable ledger persistence. | Canonical ledger persistence owner | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production deletes before non-fatal Git push; P0-A final candidate improves ordering but remote-containment edge remains. | Accepted bet disappears permanently. | ACK timestamp before remote durable commit. | Resolve final P0-A remote containment. |
| **QUEUE-002** | Queue | **P0** | Local file write/local commit is not sufficient durability for an ephemeral runner. | Remote canonical persistence | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production treats local write then delete; candidate still needed explicit remote containment proof. | Runner dies with only local state. | Remote branch containment check. | Resolve final P0-A. |
| **QUEUE-003** | Queue | **P0** | Push/rebase/remote verification failure for accepted mutation is fatal and leaves queue item retryable. | Consumer transaction | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production logs push failure non-fatally after ACK. | Data loss. | Push fail + ACK occurrence must be zero. | Resolve final P0-A. |
| **QUEUE-004** | Queue | **P0** | Transient infrastructure inability to validate a legitimate bet is RETRY, not permanent reject. | Consumer classifier | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Candidate review found bankroll-unavailable could be classified rejected. | Temporary outage deletes user action. | Retry-class item ACK count = 0. | Implement explicit ACCEPT/REJECT/RETRY. |
| **QUEUE-005** | Queue | **P1** | Permanent reject and retryable failure are explicit distinct states. | Consumer queue semantics | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production collapses invalid/failure paths. | Wrong ACK policy. | Queue decision reason metrics. | Final P0-A. |
| **QUEUE-006** | Queue | **P0** | Cancellation ACK occurs only after cancellation is durably persisted. | Ledger mutation transaction | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production cancel locally then delete queue; final candidate still under review. | Cancellation disappears/reverts. | Cancel ACK before durable remote mutation. | Final P0-A. |
| **QUEUE-007** | Queue | **P1** | Placement and cancellation can share one durable persistence boundary per consumer run. | Consumer transaction coordinator | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Not true in production; target final candidate. | Conflicting commits and partial ACKs. | Mutations per durable transaction. | Final P0-A design. |
| **QUEUE-008** | Queue | **P0** | Retry after ACK failure is idempotent and cannot duplicate ledger row. | Stable bet identity / ledger | 🟡 PARTIAL | 🟣 BRANCH PARTIAL | Production duplicate guard exists but identity is weak; P0-A improves provenance. | Duplicate stake/P&L. | Duplicate pending ID/signal identity in ledger. | Strengthen identity/outbox semantics. |
| **QUEUE-009** | Queue | **P1** | Duplicate detection should use strongest stable bet identity, not only match text/date/market. | Canonical bet identity | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Production `match_id` uses names+date and market tuple. | Different event collides or duplicate escapes. | Duplicate canonical IDs / collision detector. | Future identity hardening. |
| **QUEUE-010** | Queue | **P1** | Rejected malformed queue items have explicit reason and auditable ACK policy. | Consumer | 🟡 PARTIAL | 🟣 BRANCH PARTIAL | Production invalid items are deleted without rich durable audit. | Silent loss hides client/system defects. | Reject reason counts. | Add reject audit trail. |
| **QUEUE-011** | Queue | **P1** | Zero-pending heartbeat may refresh risk state but may not fabricate signal/odds freshness. | Risk publisher | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Target architecture from P0-A. | Heartbeat masks stale sports data. | Separate risk published_at vs signal/odds timestamps. | Final P0-A + monitoring. |
| **QUEUE-012** | Queue | **P1** | Queue processing must be per-user isolated; one user's failure must not mutate another user's state incorrectly. | User-scoped KV + ledger | 🟡 PARTIAL | 🟣 BRANCH PARTIAL | Per-user keys exist; error isolation not comprehensively proven. | Cross-user corruption. | User key/ledger mismatch monitor. | P0-C hardening. |
| **DATA-001** | Data | **P0** | Every new bet has explicit supported `sport`; sport is never inferred from generic market alone. | Bet identity schema | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production ledger lacks explicit sport field; inference used in reports. | Tennis classified as football/general. | New bet missing sport. | Finish P0-A. |
| **DATA-002** | Data | **P1** | Every new canonical Tennis Value bet has valid league/tour/category metadata as defined by schema. | Tennis identity | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Historical blank/wm2026 contamination. | Wrong reporting/provider routing. | Tennis value with invalid league/tour. | Define taxonomy + enforce. |
| **DATA-003** | Data | **P0** | Blank Tennis league must never default to `wm2026`. | Ledger migration | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production `_load` fills all blank league as wm2026. | Football contamination of Tennis. | sport=tennis + league=wm2026 default pattern. | Finish P0-A. |
| **DATA-004** | Data | **P1** | Historical compatibility behavior cannot silently rewrite semantic identity. | Ledger migration | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production migration defaults change meaning on load. | Historical truth changes by reader version. | Migration audit / row mutation detector. | Use explicit UNKNOWN/legacy flags. |
| **DATA-005** | Data | **P0** | New Value bet stores explicit `signal_id`. | Canonical signal provenance | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production ledger schema lacks it. | Cannot prove model provenance. | Value row missing signal_id. | Finish P0-A. |
| **DATA-006** | Data | **P1** | New bet stores `fixture_key` where canonical fixture identity exists. | Fixture registry | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production ledger lacks it. | Cannot join event truth robustly. | Supported row missing fixture_key. | Finish P0-A. |
| **DATA-007** | Data | **P1** | New bet stores bankroll-at-placement and risk provenance. | Risk/ledger | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production lacks fields. | Stake cannot be audited later. | Missing bankroll_at_placement. | Finish P0-A. |
| **DATA-008** | Data | **P0** | Value `model_prob` unit in ledger is probability fraction `0<p<1`. | Ledger/model measurement schema | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Production can receive arbitrary client units; P0-A normalizes percent→fraction. | Calibration contamination or omission. | Value model_prob outside open interval. | Finish P0-A. |
| **DATA-009** | Data | **P1** | Published model probability unit is explicitly documented and converted exactly once. | Publication schema | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | signals publishes percentage; multiple layers historically mixed units. | 100x EV/calibration errors. | Schema/unit contract tests. | Keep parity tests. |
| **DATA-010** | Data | **P1** | CSV and SQLite represent the same canonical bet identity and risk fields. | Ledger persistence model | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production SQLite schema omits fields/league semantics. | Different readers see different truth. | CSV↔SQLite parity test. | Finish P0-A. |
| **DATA-011** | Data | **P1** | SQLite sync failure must have defined operational consequence; silent warning cannot create indefinite divergence. | Ledger persistence | 🟡 PARTIAL | 🟡 PARTIAL | Production logs warning and continues. | Secondary DB becomes stale. | CSV/SQLite row-count/schema parity health. | P0-D/monitoring. |
| **DATA-012** | Data | **P1** | All externally published JSON schemas are versioned or backward-compatible. | Publication schema | 🟡 PARTIAL | 🟡 PARTIAL | Many additive fields, limited explicit schema versioning. | Old browser misreads new state. | Schema version/required fields check. | Introduce schema_version. |
| **DATA-013** | Data | **P1** | User-specific snapshots contain only that user's private financial state. | User isolation | 🟡 PARTIAL | 🟡 PARTIAL | Per-user writer exists; Worker fallback to default snapshot remains. | Cross-user state exposure. | Requested user vs served snapshot identity. | P0-C. |
| **DATA-014** | Data | **P1** | Canonical current bankroll definition is documented consistently (free/staked/equity). | Financial accounting schema | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Multiple representations exist. | 5% cap based on inconsistent denominator. | Bankroll recomputation parity. | Formalize accounting. |
| **DATA-015** | Data | **P1** | Signal snapshot publication never replaces good data with structurally thin/corrupt payload. | Publication writer / Worker guard | 🟡 PARTIAL | 🟡 PARTIAL | Worker has thin-payload guard with force bypass. | PWA wiped to empty/corrupt state. | Payload-size/schema anomaly. | Strengthen publisher schema validation. |
| **ODDS-001** | Odds | **P0** | `odds_state.json` remains sole writer authority for refreshed odds. | Odds state sidecar | ✅ ENFORCED | ✅ ENFORCED | Explicit module contract. | Concurrent writers create race/divergence. | Writer audit. | Preserve. |
| **ODDS-002** | Odds | **P0** | Every market refresh retrieves the quote for the exact same market/selection. | Market taxonomy + provider quote | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Production Tennis refresher maps almost every non-home market to H2H-B. | Wrong current odds/EV. | Market vs provider-field contract test. | Fix Tennis market mapping before trust score increase. |
| **ODDS-003** | Odds | **P0** | No model-implied/WebSearch-only price may be authoritative for actionable current odds unless explicitly approved by policy. | Provider authority | 🟡 PARTIAL | 🟡 PARTIAL | Football refresher fails closed on WebSearch; Tennis scanner has fallback/display mechanisms. | Synthetic/non-market quote treated as executable. | Actionable odds source whitelist. | Wave3D. |
| **ODDS-004** | Odds | **P1** | Odds source and source tier are preserved with every refreshed quote. | Odds state | ✅ ENFORCED | ✅ ENFORCED | Sidecar stores source/tier. | Cannot audit quality. | Missing source on ACTIVE. | Preserve + monitor. |
| **ODDS-005** | Odds | **P1** | Initial odds are immutable historical observation; refresh never overwrites scan entry price semantics. | Odds state | ✅ ENFORCED | ✅ ENFORCED | Sidecar seeds/preserves initial odds. | CLV/line movement corrupted. | Initial odds mutation detector. | Preserve. |
| **ODDS-006** | Odds | **P1** | Odds history is timestamped, deduplicated and market-specific. | Odds state | 🟡 PARTIAL | 🟡 PARTIAL | History exists/dedups; market identity relies on signal_id correctness. | Line history cross-market contamination. | History signal/market parity. | Strengthen identity. |
| **ODDS-007** | Odds | **P0** | Odds freshness is computed from trusted fetch timestamp, not UI/render time. | Odds state | ✅ ENFORCED | ✅ ENFORCED | Sidecar odds_ts from refresher. | Stale quote appears fresh. | Timestamp origin/schema check. | Preserve. |
| **ODDS-008** | Odds | **P1** | Provider outage degrades to non-actionable state, never fabricated ACTIVE. | Signal lifecycle | 🟡 PARTIAL | 🟡 PARTIAL | UNREFRESHABLE/STALE states exist; alternate UI bypasses on main. | Outage creates fake value. | Provider failure + actionable count. | P0-A + Wave3D. |
| **ODDS-009** | Odds | **P1** | Refresh cadence becomes faster near kickoff and is not slower than freshness guarantee. | Odds refresher | ✅ ENFORCED | ✅ ENFORCED | 5/10/15/20/30m cadence, hard stale 30m. | Freshness window breached systematically. | Due-but-not-refreshed signals. | Preserve/monitor. |
| **ODDS-010** | Odds | **P1** | EV recomputation uses model probability in correct unit exactly once. | Signal status | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Helper divides published percent by 100; historical bugs existed. | 100x EV artifact. | EV recomputation parity. | P0-A + invariant test. |
| **ODDS-011** | Odds | **P1** | Absurd/NaN EV in sidecar/published signal is sanitized and ACTIVE revoked. | Odds state | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Production corruption guard exists but loose ±500%; P0-A actionable max40. | Corrupt data actionability. | Sanitized EV counter. | Tighten trust monitor. |
| **ODDS-012** | Odds | **P1** | Closing odds correspond to the same market/selection as entry bet. | Closing-odds subsystem | ⚪ UNVERIFIED | ⚪ UNVERIFIED | Not exhaustively re-audited in this session. | CLV becomes meaningless. | Entry market vs closing source field. | Dedicated CLV audit. |
| **TEN-001** | Tennis | **P0** | Elapsed time alone never creates LIVE. | TennisEventState | ✅ ENFORCED | ✅ ENFORCED | Explicit event_state authority rule. | False LIVE. | LIVE state with no qualified evidence. | Preserve. |
| **TEN-002** | Tennis | **P0** | LIVE requires qualified authoritative evidence. | TennisEventState authority matrix | ✅ ENFORCED | ✅ ENFORCED | ESPN primary; TE informational for live. | False LIVE. | LIVE evidence source whitelist. | Preserve + Wave3D. |
| **TEN-003** | Tennis | **P1** | Initial scheduled start becomes immutable after authoritative creation. | TennisEventState | ✅ ENFORCED | ✅ ENFORCED | Separate scheduled_start_initial/current. | Historical schedule truth overwritten. | Initial-start mutation. | Preserve. |
| **TEN-004** | Tennis | **P1** | Current scheduled start changes only through authorized source rules. | TennisEventState | 🟡 PARTIAL | 🟡 PARTIAL | Authority matrix exists; source metadata integration remains audit concern. | Fallback source silently becomes primary. | Schedule update source violation. | Audit TE source/odds_source path. |
| **TEN-005** | Tennis | **P1** | Schedule truth and lifecycle truth remain separate fields. | TennisEventState | ✅ ENFORCED | ✅ ENFORCED | Explicit architecture. | Delay/reschedule conflated with LIVE. | State/schedule contradiction checks. | Preserve. |
| **TEN-006** | Tennis | **P0** | Terminal authoritative state dominates stale kickoff heuristics. | TennisEventState / signal lifecycle | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | COMPLETED/CANCELLED handled; broader cross-layer parity was P0-A focus. | Completed match still active. | Terminal event + ACTIVE signal. | P0-A + Wave3D. |
| **TEN-007** | Tennis | **P1** | Fixture identity survives cross-midnight/reschedule without generating new logical bet identity. | Fixture registry | ✅ ENFORCED | ✅ ENFORCED | Registry specifically introduced for this. | Duplicate signal/bet. | Same provider event -> multiple fixture keys. | Preserve. |
| **TEN-008** | Tennis | **P0** | Fixture identity is globally unique across event instances, years, rounds and repeat meetings. | Fixture identity | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Current key lacks year/round/event-instance. | Wrong event inherits old state/signal. | Fixture-key collision detector. | Future provider-native ID migration. |
| **TEN-009** | Tennis | **P1** | Provider-native stable event ID is preferred primary identity when available. | Fixture identity target | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Current fallback pair+sport_key dominates. | Heuristic collisions. | Native ID coverage. | Design workstream. |
| **TEN-010** | Tennis | **P1** | TennisExplorer fallback cannot be promoted to stronger schedule authority through missing/mismatched metadata. | Source authority | 🟡 PARTIAL | 🟡 PARTIAL | Known source-vs-odds_source concern not yet fully closed. | Wrong kickoff overwrites canonical schedule. | Authority field consistency. | Re-audit and test. |
| **TEN-011** | Tennis | **P1** | Tournament/category metadata is tied to each parsed fixture, not leaked from page-wide regex context. | TE parser | 🟡 PARTIAL | 🟡 PARTIAL | Historical suspicious metadata clusters. | Wrong surface/category/model gate. | Tournament-player plausibility checks. | Parser hardening. |
| **TEN-012** | Tennis | **P1** | Open Tennis bet classification uses explicit sport identity, not market/source guessing. | Ledger identity | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production live monitor has historical inference weakness; P0-A adds sport for new bets. | Bet invisible to live/settlement pipeline. | Open Tennis row with missing sport. | P0-A + historical segmentation. |
| **MODEL-001** | Model | **P0** | Only models with passed production gate may be used in live ensemble. | Model metadata | ✅ ENFORCED | ✅ ENFORCED | Tennis ensemble requires `gate_passed`. | Failed model silently deployed. | Live model metadata gate check. | Preserve. |
| **MODEL-002** | Model | **P0** | Training/validation feature semantics must match live-serving feature semantics or documented domain shift must be validated. | Feature pipeline | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Live Tennis ensemble uses fresh `RollingState()`; historical training uses progressed state. | Holdout quality overstates live model quality. | Feature distribution parity monitor. | Model Integrity workstream. |
| **MODEL-003** | Model | **P1** | Model probability is finite and bounded before signal generation. | Model output contract | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Calibrators clip some probabilities; P0-A rejects invalid bet probability. | NaN/extreme model output. | Model output domain check. | Unify contracts. |
| **MODEL-004** | Model | **P1** | Unknown/insufficient-history player cannot generate falsely confident Tennis Value signal. | Tennis ensemble | ✅ ENFORCED | ✅ ENFORCED | Known-player min-match gate returns low_confidence. | Default Elo produces fake edge. | Unknown-player actionable signal count. | Preserve. |
| **MODEL-005** | Model | **P1** | Calibration artifacts are applied only when sample/gate requirements are met. | Calibration loader | ✅ ENFORCED | ✅ ENFORCED | Meta calibrator min samples; surface calibrators optional. | Overfit calibrator distorts probabilities. | Calibrator metadata/age/sample monitor. | Preserve. |
| **MODEL-006** | Model | **P1** | Symmetric prediction removes player-order positional bias. | Tennis ensemble | ✅ ENFORCED | ✅ ENFORCED | AB/BA predictions averaged. | Order artifact changes outcome. | Swap invariance test. | Preserve. |
| **MODEL-007** | Model | **P1** | Every model artifact records feature version/training metadata. | Model metadata | 🟡 PARTIAL | 🟡 PARTIAL | Tennis LGBM writes feature_version/trained_at; coverage across all models not verified. | Unknown artifact provenance. | Artifact metadata completeness. | Expand to all models. |
| **MODEL-008** | Model | **P1** | Retraining cannot promote a model solely because it trained successfully; evaluation gate controls promotion. | Model governance | 🟡 PARTIAL | 🟡 PARTIAL | Gate concept exists; all retrain paths not fully audited. | Regression deployed. | Promotion audit trail. | P0-D. |
| **MODEL-009** | Model | **P1** | Rule-based post-model adjustments require measured evidence and versioned provenance. | Ensemble adjustments | 🟡 PARTIAL | 🟡 PARTIAL | Bayesian/altitude/style adjustments exist with comments/backtests. | Silent heuristic drift. | Adjustment version + ablation report. | Formalize. |
| **MODEL-010** | Model | **P1** | Live feature fetch failure degrades to explicit neutral/fallback state and is observable. | Tennis live features | 🟡 PARTIAL | 🟡 PARTIAL | Serve stats failures fall to neutral prior, mostly debug log. | Silent feature loss shifts model. | Feature availability telemetry. | Monitoring/model integrity. |
| **MEAS-001** | Measurement | **P0** | Production metrics include only provably canonical production Value bets. | Measurement provenance | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production report equates non-manual/non-Challenger source with value. | ROI/Brier population contaminated. | Production row without canonical signal provenance. | New schema + historical cohorting. |
| **MEAS-002** | Measurement | **P0** | Manual bets are excluded from model-approved ROI/calibration metrics. | Source/provenance | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Report separates source=manual; historical source ambiguity remains. | Manual judgment credited to model. | Manual in production population. | P0-A future rows + backfill segmentation. |
| **MEAS-003** | Measurement | **P1** | Shadow bets are excluded from production metrics based on explicit provenance, not one league heuristic. | Signal tier/provenance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Production shadow classification only Challenger league. | Other shadow experiments leak into production. | Shadow provenance field. | Measurement redesign. |
| **MEAS-004** | Measurement | **P0** | Sport classification for metrics uses explicit sport, not market-name inference. | Ledger identity | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | `_is_tennis_row()` infers from market/source/league. | Tennis Match Winner pollutes football/general stats. | Rows where inferred sport != explicit sport. | P0-A new data + historical cohort. |
| **MEAS-005** | Measurement | **P1** | Calibration metrics use only valid `0<p<1` model probabilities and track exclusion reasons. | Measurement schema | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Report filters valid p but doesn't prove why invalid rows exist. | Bad rows silently disappear. | Calibration exclusion counts by reason. | Add audit fields/report. |
| **MEAS-006** | Measurement | **P1** | CLV coverage is reported with denominator and source/market validity. | CLV pipeline | ✅ ENFORCED | ✅ ENFORCED | Season report reports coverage/hit/mean. | Sparse CLV misread as strong evidence. | Coverage threshold + market match. | Improve coverage. |
| **MEAS-007** | Measurement | **P1** | Closing-line comparison uses same proposition and bookmaker/source semantics. | CLV | ⚪ UNVERIFIED | ⚪ UNVERIFIED | Needs dedicated audit. | CLV sign/size meaningless. | Market/selection/source join validation. | Dedicated CLV workstream. |
| **MEAS-008** | Measurement | **P1** | Historical cohorts remain separable by calibration/model epoch. | Report | ✅ ENFORCED | ✅ ENFORCED | Calibration epoch split exists. | Before/after changes mixed. | Epoch metadata completeness. | Preserve/extend. |
| **MEAS-009** | Measurement | **P1** | No backfill silently changes historical model provenance. | Historical data governance | 🟡 PARTIAL | 🟡 PARTIAL | Several backfill scripts exist. | Retrospective metrics become unauditable. | Backfill manifest. | P0-D. |
| **MEAS-010** | Measurement | **P1** | Every published performance claim includes sample size and population definition. | Reporting | 🟡 PARTIAL | 🟡 PARTIAL | Core report includes n; population definition currently weak. | Small/contaminated sample overinterpreted. | Report contract. | Measurement redesign. |
| **REL-001** | Release | **P0** | Source-changing production commit must have relevant green CI. | CI gate | ✅ ENFORCED | ✅ ENFORCED | `require_green_ci.py` fail-closed exact/inherited logic. | Untested source runs production. | Source SHA without green run. | Preserve. |
| **REL-002** | Release | **P0** | Failed/active/missing ambiguous CI is not treated as green. | CI gate | ✅ ENFORCED | ✅ ENFORCED | Explicit decision logic. | Red build deployed. | Guard failure metrics. | Preserve. |
| **REL-003** | Release | **P1** | Path-excluded data-only HEAD may inherit green source ancestor only when ancestry is proven. | CI gate | ✅ ENFORCED | ✅ ENFORCED | Compare API ancestor check. | Runtime commit hides unrelated source change. | Source/runtime classifier. | Preserve. |
| **REL-004** | Release | **P1** | Source Release SHA is published separately from Runtime/Data HEAD. | Build provenance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Dashboard build info may use current git HEAD. | Users/monitor cannot identify validated source. | Public build_info with both SHAs. | P0-B/3D. |
| **REL-005** | Release | **P1** | Rollback target is explicit and tested for source releases. | Rollback governance | 🟡 PARTIAL | 🟡 PARTIAL | Rollback script exists; full deploy-unit verification not complete. | Incident recovery uncertain. | Rollback drill outcome. | P0-D. |
| **REL-006** | Release | **P1** | Worker deploy version is tied to source release SHA. | Worker release provenance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | No comprehensive evidence in current map. | Worker/main semantic drift. | Worker version endpoint/hash. | P0-B/3D. |
| **REL-007** | Release | **P1** | Pages/public PWA version is tied to source release SHA. | PWA provenance | 🟡 PARTIAL | 🟡 PARTIAL | Build info exists but runtime HEAD confusion remains. | Browser runs unknown source. | Public build SHA verification. | Wave3D. |
| **REL-008** | Release | **P1** | Critical deterministic betting safety tests are hard CI gates. | CI | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Production main CI lacks Node Worker contract; P0-A adds it. | Safety regression passes CI. | CI job contains Worker contract. | Merge P0-A. |
| **REL-009** | Release | **P1** | Browser-contract tests cover PWA safety semantics; actual browser smoke required before release closure. | Release validation | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Node pure-function tests not Playwright; real Playwright exists but final P0-A run outstanding. | UI wiring bug escapes. | Focused real-browser result. | Final P0-A. |
| **REL-010** | Release | **P1** | Runtime data bots cannot mutate source paths. | Git writer governance | 🟡 PARTIAL | 🟡 PARTIAL | Safe-push/path controls exist; architecture historically had contamination incidents. | Bot changes code unintentionally. | Bot commit changed path outside allowlist. | P0-D/Wave3D. |
| **MON-001** | Monitoring | **P0** | `status=ok` and non-zero execution exit code cannot coexist. | Health writer | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Health writer trusts caller; known workflow contradiction. | False green. | Health rows with ok + exit!=0. | P0-B. |
| **MON-002** | Monitoring | **P1** | Expected cadence definitions match actual active workflows/launchd schedules. | Health schedule authority | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Hardcoded JOB_SCHEDULE can drift from workflows. | Healthy job marked stale or dead job marked fine. | Schedule source parity. | P0-B. |
| **MON-003** | Monitoring | **P1** | Aggregate health cannot overwrite/erase valid signal payload when cloud upload fails. | Health publisher | 🟡 PARTIAL | 🟡 PARTIAL | Guard/merge logic exists. | Monitoring damages product data. | Payload integrity after health upload. | Preserve/test. |
| **MON-004** | Monitoring | **P1** | Outcome checks verify product outcomes, not only cron execution. | Outcome monitoring | 🟡 PARTIAL | 🟡 PARTIAL | Stuck bets, stale signals, push, silent settle exist. | Jobs green while product broken. | Outcome symptom coverage. | Expand. |
| **MON-005** | Monitoring | **P0** | Production Trust detects actionable signal with stale/missing/wrong-market odds. | Future Trust monitor | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Not in current health. | Unsafe bet despite green jobs. | Semantic signal sweep. | Wave3D. |
| **MON-006** | Monitoring | **P0** | Production Trust detects stake >5% or >3 active bets. | Future Trust monitor | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | No current semantic monitor. | Risk invariant violated silently. | Recompute ledger risk. | Wave3D. |
| **MON-007** | Monitoring | **P0** | Production Trust detects false Tennis LIVE / open Tennis bet missing from live system. | Future Trust monitor | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Current live system stronger but no universal trust assertion. | Incorrect live UX/settlement. | Event state vs evidence/open bet join. | Wave3D. |
| **MON-008** | Monitoring | **P1** | Production Trust detects source-release/CI/runtime-head mismatch. | Release monitor | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Not currently explicit. | Unknown production source. | Source release SHA assertion. | P0-B/Wave3D. |
| **MON-009** | Monitoring | **P1** | Production Trust detects fixture identity collisions. | Identity monitor | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | No global collision monitor. | Wrong event state reused. | Duplicate registry key with incompatible event metadata. | Wave3D. |
| **MON-010** | Monitoring | **P1** | Monitoring distinguishes DEGRADED from UNSAFE. | Trust policy | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Current aggregate has ok/degraded/down, not safety semantics. | Money-risk condition treated like cosmetic staleness. | Severity policy tests. | Wave3D. |
| **MON-011** | Monitoring | **P1** | Health check failure itself becomes visible, not silently empty-good. | Monitoring engine | 🟡 PARTIAL | 🟡 PARTIAL | Outcome checks emit checker_error warning; other readers may return empty. | Blind spot looks healthy. | Checker execution coverage. | P0-B. |
| **MON-012** | Monitoring | **P1** | Freshness heartbeats do not masquerade as semantic data freshness. | Trust timestamps | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Multiple updated/heartbeat timestamps exist. | Stale odds/signals hidden by unrelated heartbeat. | Timestamp provenance checks. | P0-B/Wave3D. |
| **SEC-001** | Security | **P0** | Personal betting ledger is not publicly exposed. | Private financial datastore | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Repo is public and per-user ledger is tracked. | Privacy breach. | Public path scanner for ledger/user financial files. | P0-C. |
| **SEC-002** | Security | **P0** | Legal/privacy text matches actual persistence behavior. | Legal/data architecture | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Legal says bankroll/bet log localStorage-only while backend ledger exists. | Misleading privacy disclosure. | Policy-vs-data-map review. | P0-C + legal review. |
| **SEC-003** | Security | **P0** | User-specific signal/financial state never falls back to another user's private state. | User isolation | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Worker can fallback missing per-user snapshot to default user. | Cross-user disclosure. | Requested user != payload owner. | P0-C. |
| **SEC-004** | Security | **P1** | User tokens are scoped, revocable and never exposed in URLs/loggable query strings. | Auth boundary | 🟡 PARTIAL | 🟡 PARTIAL | Token rotation exists; complete browser transport audit not finished. | Credential leakage. | Token-location audit. | P0-C. |
| **SEC-005** | Security | **P1** | Master token is never exposed to browser clients. | Worker auth | 🟡 PARTIAL | 🟡 PARTIAL | Architecture distinguishes master/per-user; live secret handling not reverified tonight. | Total backend compromise. | Secret exposure scan. | P0-C. |
| **SEC-006** | Security | **P1** | Per-user authorization controls every read/write queue and signal operation. | Worker auth | 🟡 PARTIAL | 🟡 PARTIAL | Per-user KV routing exists; fallback semantics weaken isolation. | Cross-user mutation/read. | Authorization matrix tests. | P0-C. |
| **SEC-007** | Security | **P1** | Push subscriptions are user/privacy scoped and have deletion lifecycle. | Push subsystem | 🟡 PARTIAL | 🟡 PARTIAL | KV push_subs exists; expiry pruning/outcome checks exist. | Persistent endpoint exposure. | Subscription ownership/expiry monitor. | P0-C. |
| **SEC-008** | Security | **P1** | Public Pages contains no secrets/private operational artifacts. | Static publication boundary | 🟡 PARTIAL | 🟡 PARTIAL | No known secret claim from current audit, but privacy data coupling exists. | Credential/data exposure. | Public artifact allowlist scan. | P0-C. |
| **SEC-009** | Security | **P1** | Changing repository visibility cannot silently break public PWA availability. | Deployment/privacy migration | 🟡 PARTIAL | 🟡 PARTIAL | Pages/repo coupling requires planned migration. | Privacy fix causes outage. | Migration rehearsal. | P0-C. |
| **SEC-010** | Security | **P1** | Multi-user identity has explicit owner metadata in every private snapshot/ledger. | Identity schema | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Filename/KV key imply user; payload ownership metadata not universal. | Misrouting undetectable. | owner/user_id field parity. | P0-C. |
| **GOV-001** | Governance | **P0** | ChatGPT/CEO is read-only to GitHub/project; no mutations. | Human governance | ✅ ENFORCED | ✅ ENFORCED | Explicit operating rule. | Auditor independence lost. | Audit tool usage policy. | Preserve. |
| **GOV-002** | Governance | **P0** | Claude/authorized Builder is sole normal source-code mutator. | Builder governance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | `auto_heal_ai.py` can autonomously edit/commit/push scripts. | Unreviewed autonomous source mutation. | Source commit actor/path audit. | P0-D. |
| **GOV-003** | Governance | **P0** | Autonomous healer may not bypass code review/release governance for source changes. | Recovery governance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | AI healer applies FIX then commits/pushes after pytest. | AI-generated production mutation. | Auto-heal source commit detector. | P0-D. |
| **GOV-004** | Governance | **P0** | No auto-betting / implicit logging of real bets without explicit user action. | CEO rule | 🟡 PARTIAL | 🟡 PARTIAL | No broad proof of active autobetting; historical auto-log mechanisms governed by tests. | Unapproved financial record/action. | New ledger source without user/approved scanner semantics. | Keep hard regression. |
| **GOV-005** | Governance | **P1** | Hard CEO safety invariants are not ordinary user-overridable tuning flags. | Policy architecture | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Config mixes rollout/user modes and policy; `--all-live` exists. | Operator bypasses safety. | Override use audit. | P0-D. |
| **GOV-006** | Governance | **P1** | Tennis live/shadow rollout must be justified by gate evidence, not one-off user override. | Model/rollout governance | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Production config broadly forces live categories. | Unvalidated category bets enter production. | Live category without gate artifact. | P0-D. |
| **GOV-007** | Governance | **P1** | Every production source change has explicit rollback reference. | Release governance | 🟡 PARTIAL | 🟡 PARTIAL | Rollback rule/process exists but not universal artifact. | Slow unsafe rollback. | Release manifest completeness. | P0-D. |
| **GOV-008** | Governance | **P1** | Backfills/migrations are auditable, reversible or explicitly immutable-preserving. | Data governance | 🟡 PARTIAL | 🟡 PARTIAL | Many backfill scripts; no single migration ledger. | Historical truth silently changed. | Migration manifest. | P0-D. |
| **GOV-009** | Governance | **P1** | CEO score increases only for production evidence; branch work is projected separately. | CEO governance | ✅ ENFORCED | ✅ ENFORCED | New canonical scorecard rule. | Score inflation hides risk. | Scorecard audit. | Preserve. |
| **GOV-010** | Governance | **P1** | Builder reports are evidence inputs, never substitutes for independent CEO verification. | CEO/Builder process | ✅ ENFORCED | ✅ ENFORCED | Repeated P0-A reviews caught report/code mismatches. | False completion accepted. | Independent SHA/diff/CI review. | Preserve. |
| **OPS-001** | Operations | **P0** | PWA remains continuously usable during refactor/deployment. | Product operations | 🟡 PARTIAL | 🟡 PARTIAL | Explicit CEO rule; not every release path has live browser proof. | User-facing outage. | Public PWA availability check. | Release gate. |
| **OPS-002** | Operations | **P1** | Atomic file writes protect shared JSON/ledger artifacts against partial writes. | Persistence utilities | 🟡 PARTIAL | 🟡 PARTIAL | Atomic IO/file locks exist in key paths. | Corrupt JSON/CSV. | Parse failure/atomic writer coverage. | Expand. |
| **OPS-003** | Operations | **P1** | Concurrent Git/runtime writers have path-scoped conflict policy. | Git operations | 🟡 PARTIAL | 🟡 PARTIAL | Safe-push logic and workflow concurrency exist after incidents. | Lost/overwritten runtime state. | Conflict/retry telemetry. | P0-D. |
| **OPS-004** | Operations | **P1** | Cloud publication failure is observable and does not silently claim success. | Publisher | 🟡 PARTIAL | 🟡 PARTIAL | Various paths log failures, some non-fatal. | PWA stale despite green job. | Publish outcome health. | P0-B. |
| **OPS-005** | Operations | **P1** | Every critical external provider has explicit timeout/retry/fallback/fail-closed policy. | Provider layer | 🟡 PARTIAL | 🟡 PARTIAL | Retry helpers/provider chains exist; full inventory not verified. | Hang or bad fallback. | Provider latency/error/fallback monitor. | Provider reliability workstream. |
| **OPS-006** | Operations | **P1** | Local launchd runtime state is separately observable from GitHub Actions state. | Runtime monitoring | 🟡 PARTIAL | 🟡 PARTIAL | Historical reality snapshot showed both; repo health doesn't prove local runtime. | Local job dead while cloud healthy. | Runtime source field / heartbeat origin. | P0-B. |
| **OPS-007** | Operations | **P1** | No single bot can continuously move `main` in a way that invalidates source-release provenance. | Git runtime architecture | 🔴 NOT ENFORCED | 🔴 NOT ENFORCED | Frequent tennis runtime commits move HEAD every minutes. | PR mergeability/source identity noise. | Runtime commit rate/source release marker. | P0-D architecture decision. |
| **OPS-008** | Operations | **P1** | Disaster recovery identifies durable sources for ledger, model, config, Worker and public assets separately. | Recovery | ⚪ UNVERIFIED | ⚪ UNVERIFIED | Partial rollback tooling; full DR model not audited. | Recovery restores inconsistent components. | DR drill/manifests. | Future ops workstream. |
| **UX-001** | Product | **P0** | UI labels distinguish scan odds from current executable odds. | PWA | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | Some displays distinguish; production model-tip actions blur semantics. | User believes stale scan price is current. | Rendered label vs payload odds. | P0-A. |
| **UX-002** | Product | **P0** | Disabled/non-actionable signal remains informative without misleading Value CTA. | PWA | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | P0-A target manual/informational fallback. | Fail-closed becomes unusable or misleading. | CTA semantics browser test. | P0-A. |
| **UX-003** | Product | **P1** | Manual action is clearly labeled as manual and not model-approved. | PWA | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | P0-A explicit flow candidate. | User confuses judgment bet with SportsBrain signal. | Manual badge/source. | P0-A. |
| **UX-004** | Product | **P1** | Zero actionable signals is a valid usable app state, not an error/fail-open trigger. | PWA | 🟡 PARTIAL | 🔵 BRANCH CANDIDATE | P0-A tests target zero-signal usability. | System fabricates action to avoid empty UI. | Zero-signal browser smoke. | P0-A. |
| **UX-005** | Product | **P1** | User sees meaningful degraded/stale state rather than silent outdated data. | PWA/health | 🟡 PARTIAL | 🟡 PARTIAL | Stale banner exists; semantic trust incomplete. | User acts on stale system. | Degraded banner tied to trust state. | Wave3D. |
| **UX-006** | Product | **P1** | Open/pending/settled/cancelled bet lifecycle is clearly represented and consistent with backend. | PWA + ledger | 🟡 PARTIAL | 🟣 BRANCH PARTIAL | Pending UI exists; durability semantics still being hardened. | UI says synced when not durable. | Lifecycle state parity. | P0-A/P0-B. |
| **UX-007** | Product | **P1** | Browser error paths never silently convert Value action into another semantic. | PWA | 🔴 NOT ENFORCED | 🔵 BRANCH CANDIDATE | Historical alternate paths/coercions; P0-A improves. | User intent changes invisibly. | Browser request source/identity assertion. | P0-A. |
| **UX-008** | Product | **P1** | Public PWA release gets real-browser verification on final deployed assets. | Release UX | 🔴 NOT ENFORCED | 🟣 BRANCH PARTIAL | Real Playwright exists locally; final P0-A focused run pending and public fetch historically limited. | Repo tests pass but deployed PWA broken. | Public smoke evidence. | Release closure. |---

# 5. Immediate P0 closure queue

The following P0 invariants are known **not enforced in production** at this snapshot:

- **BET-001 — Every `source=value` bet must resolve to one real canonical signal by `signal_id`.**  
  Owner: Canonical published signal registry  
  Closure: Finish P0-A and verify Worker/public flow.
- **BET-002 — Canonical signal identity must bind match, market, sport and fixture identity; client may request but not redefine it.**  
  Owner: Canonical signal  
  Closure: Finish P0-A; add invariant monitor.
- **BET-003 — Only exact sources `value` and `manual` are accepted; unknown input must not normalize to `value`.**  
  Owner: Bet API contract  
  Closure: Finish P0-A.
- **BET-005 — All Value actionability surfaces must use the same semantic contract.**  
  Owner: Canonical actionability policy  
  Closure: Finish P0-A; preserve parity tests.
- **BET-007 — Value bet must use actual `current_odds`, never scan-time odds presented as current.**  
  Owner: Odds-state authority  
  Closure: Finish P0-A.
- **BET-010 — Materially future `odds_ts` must fail closed; limited clock skew only.**  
  Owner: Odds-state authority  
  Closure: Finish P0-A.
- **BET-015 — Tennis Value signals require explicit canonical event status.**  
  Owner: TennisEventState  
  Closure: Finish P0-A.
- **RISK-001 — Final stake must be <= 5% of authoritative current bankroll.**  
  Owner: Ledger-derived bankroll / hard CEO invariant  
  Closure: Finish P0-A + monitor.
- **RISK-002 — 5% rule applies to both Value and Manual bets.**  
  Owner: Hard risk policy  
  Closure: Finish P0-A.
- **RISK-003 — Worker must not trust client-supplied bankroll as security authority.**  
  Owner: Backend risk state  
  Closure: Finish P0-A.
- **RISK-004 — Consumer independently revalidates bankroll cap from live ledger state.**  
  Owner: Ledger  
  Closure: Finish P0-A.
- **RISK-005 — Maximum active bets is 3 across every placement boundary.**  
  Owner: Hard CEO invariant  
  Closure: Finish P0-A.
- **RISK-006 — Worker active-bet count comes from trusted backend state plus pending queue, never client count.**  
  Owner: Published risk state + KV pending  
  Closure: Finish P0-A.
- **RISK-007 — If authoritative bankroll/open-bet state is missing or stale, new money actions fail closed.**  
  Owner: Backend risk state  
  Closure: Finish P0-A.
- **RISK-009 — Security boundaries reject oversized confirmed stake; they do not silently mutate it after user confirmation.**  
  Owner: Worker/consumer  
  Closure: Finish P0-A.
- **QUEUE-001 — Accepted pending bet may be ACKed/deleted only after durable ledger persistence.**  
  Owner: Canonical ledger persistence owner  
  Closure: Resolve final P0-A remote containment.
- **QUEUE-002 — Local file write/local commit is not sufficient durability for an ephemeral runner.**  
  Owner: Remote canonical persistence  
  Closure: Resolve final P0-A.
- **QUEUE-003 — Push/rebase/remote verification failure for accepted mutation is fatal and leaves queue item retryable.**  
  Owner: Consumer transaction  
  Closure: Resolve final P0-A.
- **QUEUE-004 — Transient infrastructure inability to validate a legitimate bet is RETRY, not permanent reject.**  
  Owner: Consumer classifier  
  Closure: Implement explicit ACCEPT/REJECT/RETRY.
- **QUEUE-006 — Cancellation ACK occurs only after cancellation is durably persisted.**  
  Owner: Ledger mutation transaction  
  Closure: Final P0-A.
- **DATA-001 — Every new bet has explicit supported `sport`; sport is never inferred from generic market alone.**  
  Owner: Bet identity schema  
  Closure: Finish P0-A.
- **DATA-003 — Blank Tennis league must never default to `wm2026`.**  
  Owner: Ledger migration  
  Closure: Finish P0-A.
- **DATA-005 — New Value bet stores explicit `signal_id`.**  
  Owner: Canonical signal provenance  
  Closure: Finish P0-A.
- **ODDS-002 — Every market refresh retrieves the quote for the exact same market/selection.**  
  Owner: Market taxonomy + provider quote  
  Closure: Fix Tennis market mapping before trust score increase.
- **TEN-008 — Fixture identity is globally unique across event instances, years, rounds and repeat meetings.**  
  Owner: Fixture identity  
  Closure: Future provider-native ID migration.
- **MODEL-002 — Training/validation feature semantics must match live-serving feature semantics or documented domain shift must be validated.**  
  Owner: Feature pipeline  
  Closure: Model Integrity workstream.
- **MEAS-001 — Production metrics include only provably canonical production Value bets.**  
  Owner: Measurement provenance  
  Closure: New schema + historical cohorting.
- **MEAS-004 — Sport classification for metrics uses explicit sport, not market-name inference.**  
  Owner: Ledger identity  
  Closure: P0-A new data + historical cohort.
- **MON-001 — `status=ok` and non-zero execution exit code cannot coexist.**  
  Owner: Health writer  
  Closure: P0-B.
- **MON-005 — Production Trust detects actionable signal with stale/missing/wrong-market odds.**  
  Owner: Future Trust monitor  
  Closure: Wave3D.
- **MON-006 — Production Trust detects stake >5% or >3 active bets.**  
  Owner: Future Trust monitor  
  Closure: Wave3D.
- **MON-007 — Production Trust detects false Tennis LIVE / open Tennis bet missing from live system.**  
  Owner: Future Trust monitor  
  Closure: Wave3D.
- **SEC-001 — Personal betting ledger is not publicly exposed.**  
  Owner: Private financial datastore  
  Closure: P0-C.
- **SEC-002 — Legal/privacy text matches actual persistence behavior.**  
  Owner: Legal/data architecture  
  Closure: P0-C + legal review.
- **SEC-003 — User-specific signal/financial state never falls back to another user's private state.**  
  Owner: User isolation  
  Closure: P0-C.
- **GOV-002 — Claude/authorized Builder is sole normal source-code mutator.**  
  Owner: Builder governance  
  Closure: P0-D.
- **GOV-003 — Autonomous healer may not bypass code review/release governance for source changes.**  
  Owner: Recovery governance  
  Closure: P0-D.

---

# 6. P0 invariants with partial production enforcement

- **BET-004 — Manual betting must be an explicit user-selected flow; invalid Value requests cannot silently downgrade to manual.**  
  Owner: PWA/Worker contract  
  Closure: Finish P0-A.
- **BET-006 — Value actionability requires `signal_status == ACTIVE`.**  
  Owner: Signal lifecycle  
  Closure: Finish P0-A.
- **BET-008 — `current_odds` must be finite and >1.0.**  
  Owner: Odds-state authority  
  Closure: Finish canonical contract.
- **BET-009 — Value odds must be fresh within canonical 30-minute hard window.**  
  Owner: Odds-state authority  
  Closure: Finish P0-A + Wave3D check.
- **BET-011 — Value `current_ev_pct` must be finite, positive and <= canonical MAX_EV (40%).**  
  Owner: Canonical gate/config  
  Closure: Finish P0-A and monitor.
- **BET-012 — Shadow signals are never actionable Value bets.**  
  Owner: Signal provenance  
  Closure: Canonical contract + measurement provenance.
- **BET-013 — Unsupported signals are never actionable Value bets.**  
  Owner: Signal contract  
  Closure: Finish P0-A.
- **BET-014 — `edge_lost`, stale, no-bet or unrefreshable state must never remain actionable.**  
  Owner: Signal lifecycle  
  Closure: Finish P0-A.
- **BET-016 — Tennis LIVE/COMPLETED/POSTPONED/CANCELLED/UNKNOWN are non-actionable.**  
  Owner: TennisEventState  
  Closure: Finish P0-A.
- **QUEUE-008 — Retry after ACK failure is idempotent and cannot duplicate ledger row.**  
  Owner: Stable bet identity / ledger  
  Closure: Strengthen identity/outbox semantics.
- **DATA-008 — Value `model_prob` unit in ledger is probability fraction `0<p<1`.**  
  Owner: Ledger/model measurement schema  
  Closure: Finish P0-A.
- **ODDS-003 — No model-implied/WebSearch-only price may be authoritative for actionable current odds unless explicitly approved by policy.**  
  Owner: Provider authority  
  Closure: Wave3D.
- **TEN-006 — Terminal authoritative state dominates stale kickoff heuristics.**  
  Owner: TennisEventState / signal lifecycle  
  Closure: P0-A + Wave3D.
- **MEAS-002 — Manual bets are excluded from model-approved ROI/calibration metrics.**  
  Owner: Source/provenance  
  Closure: P0-A future rows + backfill segmentation.
- **GOV-004 — No auto-betting / implicit logging of real bets without explicit user action.**  
  Owner: CEO rule  
  Closure: Keep hard regression.
- **OPS-001 — PWA remains continuously usable during refactor/deployment.**  
  Owner: Product operations  
  Closure: Release gate.
- **UX-001 — UI labels distinguish scan odds from current executable odds.**  
  Owner: PWA  
  Closure: P0-A.
- **UX-002 — Disabled/non-actionable signal remains informative without misleading Value CTA.**  
  Owner: PWA  
  Closure: P0-A.

---

# 7. Domain inventory

- **Betting:** 20
- **Data:** 15
- **Monitoring:** 12
- **Odds:** 12
- **Queue:** 12
- **Tennis:** 12
- **Governance:** 10
- **Measurement:** 10
- **Model:** 10
- **Release:** 10
- **Risk:** 10
- **Security:** 10
- **Operations:** 8
- **Product:** 8

---

# 8. How to use this registry for every future Builder task

A Claude/Builder prompt should not restate the entire SportsBrain architecture.

Instead it should reference the affected invariant IDs.

Example:

```text
Task: close QUEUE-001, QUEUE-002, QUEUE-003.

Do not change unrelated invariants.
For each invariant:
- identify canonical owner
- implement enforcement
- add deterministic test
- preserve failure semantics
- report evidence
```

This keeps prompts short **without losing quality**, because the invariant definition remains stable outside the conversational prompt.

---

# 9. Merge/closure protocol for an invariant

An invariant moves to `✅ ENFORCED` only when:

1. source implementation is reviewed against the invariant
2. deterministic test exercises the real production path
3. exact relevant SHA CI is green
4. branch is merged
5. production/deployed artifact is verified
6. public/runtime behavior is verified when applicable
7. a production monitor exists for high-risk invariants, or a tracked monitor gap is explicitly accepted.

Until then:
- branch-only implementation stays 🔵 or 🟣
- production status does not increase.

---

# 10. Required monitoring taxonomy

Every invariant monitor should eventually emit one of:

- `OK`
- `DEGRADED`
- `UNSAFE`
- `UNKNOWN`

Suggested semantics:

### `UNSAFE`
Use when:
- financial/risk invariant violated
- wrong quote attached to actionable market
- LIVE/terminal signal actionable
- queue acknowledged before durable financial mutation
- source release not validated
- cross-user private state exposed.

### `DEGRADED`
Use when:
- provider fallback is safe but lower quality
- informational artifact stale
- optional feature unavailable
- CLV coverage incomplete
- non-critical push delivery impaired.

### `UNKNOWN`
Use when:
- the monitor cannot obtain authoritative state.
For P0 actionability/risk, UNKNOWN must generally **fail closed**.

---

# 11. CEO top invariants by leverage

These are the invariants most likely to unlock a meaningful score increase:

1. **QUEUE-001/002/003/004/006** — financial queue durability and retry semantics.
2. **BET-001/005/007/009/015/016** — one canonical end-to-end Value contract.
3. **RISK-001/003/004/005/007** — 5%, max-three, authoritative server risk state.
4. **ODDS-002** — exact Tennis market/quote correctness.
5. **DATA-001/003/005/008/010** — explicit bet provenance and storage parity.
6. **MON-001/002/005/006/007/008** — Monitoring Truth / Production Trust.
7. **SEC-001/002/003** — privacy and user isolation.
8. **MODEL-002** — Tennis train/live feature parity.
9. **MEAS-001/003/004** — trustworthy production performance population.
10. **GOV-002/003/005/006** — controlled source mutation and rollout governance.

---

# 12. Evidence discipline / caveats

This registry was built from:
- direct read-only repository inspection
- prior independent CEO PR reviews
- the current production main snapshot
- the current P0-A PR overlay where explicitly labeled.

It does **not** silently assume:
- current local launchd state
- current Cloudflare KV values
- deployed Worker version
- current rendered browser state
- external provider health.

Those require runtime verification.

A future source change that touches an invariant owner invalidates the old implementation evidence until re-reviewed.

---

# 13. Permanent CEO rule

> **No hard invariant is “done” because a developer says it is done.**

Closure requires evidence at the actual boundary.

This registry exists specifically to prevent repeated rediscovery of the same requirements and to reduce Builder token consumption without reducing specification quality.
