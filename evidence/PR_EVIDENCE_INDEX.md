---
id: PR-EVIDENCE-INDEX
type: evidence-index
tier: warm
status: current
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: release-bound
canonical: true
---
# PR / Evidence Index

Only meaningful source changes are indexed. Automated runtime/data commits are
not architectural events and remain represented by the runtime-data SHA in the
current state card.

| PR | Domain | Exact source head / merge SHA | State at audit | Finding |
|---:|---|---|---|---|
| #188 | Nations League public delivery | `4a15f13c91e0a3f480eecbe7d4f1d9a8d4696f5e` | merged on main | Public shadow path |
| #192 | Nations League iSports | `733f76ef184388b0b980d81b33afae82d3c34b21` | merged on main | Exact odds coverage contract |
| #197 | Nations League retention | `7c784941038c117575543314ccecb0faab116e07` | merged on main | Preserve validated public snapshot |
| #199 | Worker republish | `1d1c06b945afb81f9c3d598d70c807678e8d234e` | merged on main | Manual recovery path |
| #203 | Worker validator | `b9b587c3e0c57db06da963458ff6ca61e837eabb` | merged on main | Decimal precision parity |
| #205 | Nations League shadow | `6f9f420612acfd3d05b0518d91c6d8789011847c` | merged on main | Frozen shadow candidates |
| #207 | PWA | `54b0a7b7180a2c9395d399be7cbe80773e25ee89` | merged on main | Home schedule integration |
| #209 | PWA | `9d3c2b550ca1b7b4e90b5d338a0ca5b1563d654b` | merged on main | Match detail integration |
| #210 | Cloudflare observability | `c6a7b7ed0c0824276650f241ec41ca53a27e63b7` | merged on main | Workers Logs configuration |
| #221 | Product analytics | `b67fde78e82ce169f9b23f109818ffca0ce0db20` | open / branch-only | PostHog PWA analytics; exact-head CI passed, no deploy |
| #10 | Memory operational KB | see [[evidence/PR10_RETARGET]] | open / retargeted to `main` | Main merge-base verified; local CI added; not merged |

## Evidence handling

For each entry retain the PR URL, exact tested head, CI result, merge state,
production evidence (if any), and supersession relationship. A branch head is
never silently presented as current production truth.
