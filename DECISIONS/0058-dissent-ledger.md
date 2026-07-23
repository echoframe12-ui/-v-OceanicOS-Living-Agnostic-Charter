# 0058 — The Dissent Ledger

## Context

*Dissent is data* is one of the platform's five core axioms — "disagreement
between models is the primary signal, not noise to be suppressed." The consensus
panel (`/models/consensus`) surfaced disagreement on each call, but then threw it
away: the verdicts were computed, returned, and forgotten. The one signal the
Doctrine names as *primary* was the one signal the platform kept no record of.
There was no way to ask "how often does the panel disagree?" or "is dissent
trending up?" — the data existed for a moment and evaporated.

## Decision

Persist every panel evaluation in a dissent ledger.

- A new `consensus_log.py` (a separate table, the same discipline as the
  drift-audit and CVI-history logs) records each evaluation: the prompt's
  **SHA-256 only** (never its text), the adapter count, the majority verdict, a
  `dissent` flag, a numeric `dissent_score`, the verdicts, and a timestamp.
- `dissent_score` is the fraction of *opinionated* verdicts (abstentions excluded)
  falling outside the plurality — `0.0` unanimous, `0.5` for a 2–2 split — a
  disagreement measure distinct from `consensus_delta` (which is a confidence
  adjustment, a different thing).
- `/models/consensus` records each call and returns the `dissent_score`;
  `GET /consensus/history` and `/consensus/stats` expose the trend and the
  aggregate (evaluation count, dissent rate, mean split); `/metrics` gains
  `oceanicos_dissent_rate`.

## Consequences

- The axiom is now literally true: dissent is *data*. Verified live, four
  evaluations record `dissent_rate 1.0` and `mean_dissent_score 0.25`, the history
  carries each majority and score, and `oceanicos_dissent_rate` is scrapeable
  beside the CVI and source coverage — disagreement is a first-class, trended,
  observable signal rather than a transient field.
- Storing only the prompt's hash makes the ledger a safe aggregate: it remembers
  *that* the panel disagreed and *how much*, never *what about*. `/consensus/*` can
  therefore be public and aggregate like `/cvi` and `/metrics`, exposing the
  dissent trend without exposing any prompt.
- It is a separate append-only table, so recording dissent touches neither the
  attestation chain nor its hashes — the tamper-evident record is unchanged, and
  the dissent ledger sits beside it as its own history, exactly as the drift-audit
  and held-review logs do.
- `dissent_score` is deliberately not `consensus_delta`: the delta moves a build's
  *confidence* (approve raises, revise lowers), while the score measures the
  *spread* of opinion. Conflating them would hide the distinction the axiom cares
  about — how divided the panel was, independent of which way it leaned.
