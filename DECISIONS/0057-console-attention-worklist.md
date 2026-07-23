# 0057 — Console Attention Worklist

## Context

Round 56 (`DECISIONS/0056`) added `GET /attestations/attention`, the steward's
prioritized worklist — pending held items ranked SLA-breached first, then least
confident, then oldest. But the console's Held Review panel still rendered the
held queue in plain id order from `/attestations/held`. The ranking existed in the
API and was invisible in the operator's own terminal, the same gap the API/console
split has closed before (subject history, source coverage): a capability shipped
but not surfaced where the human works.

## Decision

Surface the attention worklist at the top of the Held Review panel.

- A `⚑ work these first:` list loads `/attestations/attention?limit=5` with the
  steward token and shows the top pending items in rank order, each with the
  signals behind its position: a `BREACH`/`ok` SLA flag, the confidence (red below
  `0.5`), and `sourced`/`no source`.
- The full held table (with its release/uphold actions and per-item SLA aging)
  stays below unchanged — the worklist says *what to do first*, the table is
  *where you act*.
- The worklist refreshes with the queue after every review, so it shrinks as
  decisions are made.

## Consequences

- The "human routing" promise is now actionable in the console, not just the API:
  verified live in a browser, a steward identifying with their token sees
  `1. BREACH · conf 0.62 · sourced · OLD-charter-clause`, then
  `2. ok · conf 0.31 · no source · fresh-unsourced`, then the fresher item — the
  exact ranking `/attestations/attention` computes, with the breach at the top and
  the least-confident next.
- Presentation only, a thin client over the round-56 endpoint — no new state, no
  new ranking logic in the UI (the server ranks; the console renders), the same
  console discipline held throughout (`DECISIONS/0034`). The `/` route still
  renders and every other panel still loads.
- The worklist and the full table are deliberately both present: the worklist is a
  compact triage cue capped at five, the table remains the complete, actionable
  record with review buttons and resolution status. One tells the steward where to
  look; the other is where the work happens.
- The colour vocabulary matches the platform's line — breach and sub-`0.5`
  confidence and missing evidence read red, evidence reads green — so the worklist
  is legible at a glance in the same terms as the status board and the rest of the
  console.
