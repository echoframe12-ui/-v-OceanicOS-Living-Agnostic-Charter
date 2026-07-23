# 0059 — Console Dissent Trend

## Context

Round 58 (`DECISIONS/0058`) made dissent data — a persistent ledger with a rate
and a mean split, exposed at `/consensus/history`, `/consensus/stats`, and on
`/metrics`. But the console's Consensus panel still showed only the current
call's verdicts and a `DISSENT`/`CONSENSUS` flag. The panel that exists to make
*disagreement the output* could not show how much this evaluation split, nor
whether the panel disagrees often — the recorded dissent was invisible in the one
place an operator convenes the panel.

## Decision

Surface the dissent score and the ledger trend in the Consensus panel.

- The result head now carries the `dissent_score` the endpoint returns —
  `DISSENT … (split 0.25)` — so a single evaluation shows *how* divided the panel
  was, not just that it was.
- A dissent-trend line loads `/consensus/stats` and reads
  `dissent ledger: N evals · rate X% · mean split Y`, colour-flagged when the
  rate is high. It loads on page open (from existing history) and refreshes after
  each panel is convened.

## Consequences

- The axiom is now legible where it is enacted: verified live in a browser, the
  panel head reads `DISSENT — panel disagrees … (split 0.25)` with one of four
  members dissenting, and the trend line reads `dissent ledger: 4 evals · rate
  100% · mean split 0.25`, incrementing as panels are convened. An operator sees
  both this disagreement and the platform's disagreement over time.
- Presentation only — a thin client over the round-58 endpoints, the score coming
  straight from the `/models/consensus` response and the trend from
  `/consensus/stats`, no new state and no UI-side computation. The `/` route still
  renders and every other panel loads.
- The trend loads on boot from existing history, so the ledger is visible before
  the operator convenes anything — the panel arrives already showing what the
  record knows, consistent with the other console panels that hydrate on load.
- With this, all four recorded trust dimensions have a console home: confidence
  (the CVI sparkline), integrity (the drift-audit trail), evidence (the Stats
  panel's sourced row), and now dissent (the Consensus panel's trend) — the
  operator can read every axis the platform trends, in the terminal, at a glance.
