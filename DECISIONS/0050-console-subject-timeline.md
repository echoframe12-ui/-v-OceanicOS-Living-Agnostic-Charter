# 0050 — Console Subject Timeline

## Context

Round 46 (`DECISIONS/0046`) added per-subject attestation history — the timeline
of trust in one artifact over time — as `GET /attestations/history?subject=…`.
But it lived only in the API. The operator console, the platform's working face,
could search the ledger and pull a per-item receipt, yet had no way to follow a
single subject across its re-verifications. The capability that best tells the
platform's story — an artifact first *held*, then *earned* — was invisible in the
place an operator actually looks.

## Decision

Surface the subject timeline as an interactive console panel.

- A **Subject // Timeline** panel takes an exact subject and calls
  `/attestations/history?subject=…`, rendering the header summary (count,
  reverified vs. single, ever-held) and the confidence trend
  (`first → latest`, with a coloured ▲/▼/· delta), above a table of every
  attestation for that subject oldest to newest — id, status, confidence, time.
- It mirrors the existing Receipt and Search panels exactly: same markup, same
  `fetchJson` helper, same colour vocabulary (`ok`/`bad`/`dim`), so it reads as
  part of the console rather than bolted on.

## Consequences

- The platform's central thesis is now visible where it matters: verified live in
  a browser, tracing `living-charter` shows `held 0.42 → held 0.71 → attested
  0.93`, a green `▲ 0.51` trend, `held at some point` in red, and the three rows
  in order — "validated hesitation, then earned trust" made legible in the
  operator's own terminal, not just a JSON payload.
- Presentation only — a thin client over the existing round-46 endpoint, adding
  no state and no new server logic, the same console discipline held throughout
  (`DECISIONS/0034`): the UI reads the record, it never restates it. The `/`
  route still renders and every other panel still loads (no JS regression).
- The panel is deliberately exact-match, matching the endpoint: the Search panel
  already offers `subject contains…` for fuzzy discovery, so the timeline is the
  precise trace of one known artifact rather than an accidental grouping.
- With this, the three read-axes onto the record all have a console home — the
  Search panel (by field), the Receipt panel (by id), and now the Timeline panel
  (by subject over time) — so an operator can interrogate trust the same three
  ways the API allows.
