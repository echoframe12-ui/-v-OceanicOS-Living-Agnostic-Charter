# 0056 — Steward Attention Queue

## Context

The Doctrine's Product layer promises *human routing*, and the held-review
workflow (`DECISIONS/0018`) with its aging SLA (`0019`) makes it real: held items
below the confidence threshold wait for a steward. But `/attestations/held` only
*lists* the queue — it does not say what to work first. A steward facing a long
held queue had to eyeball SLA state, confidence, and evidence across every row to
find the most urgent item. The routing existed; the prioritization did not.

## Decision

Add `GET /attestations/attention` — the steward's ranked worklist.

- It returns only *pending* held items (not yet released or upheld) — the work
  that actually remains — each enriched with the signals behind its rank:
  `sla_breached`, `age_seconds`, `confidence`, and whether it `sourced` evidence.
- The ranking is **SLA-breached first** (the hard deadline), **then least
  confident** (the biggest risk), **then oldest** (a fair-queue tiebreaker). A
  steward works from the most overdue and least trustworthy down.
- `?limit=` caps the list; admin only, like the held queue it prioritizes.

## Consequences

- The queue is now actionable, not just visible: verified live, an SLA-breached
  item at confidence `0.6` outranks a fresher, less-confident `0.3` item, because
  the breach is the hard deadline — while among items still within SLA, the
  least-confident comes first. The steward's next action is the top row.
- Releasing an item removes it from the attention queue immediately (it is no
  longer pending), so the worklist shrinks as decisions are made — the queue
  reflects work *remaining*, not work *ever*.
- The ordering rule is deliberate and documented: breach dominates because the SLA
  is a commitment with a clock; confidence comes next because a held item at `0.3`
  is a larger risk than one at `0.6`; age is only a tiebreaker. Reasonable
  operators could weight these differently, so the endpoint states its rule rather
  than hiding it.
- Composition, not new state: the attention queue reads the same `held()`,
  released-id credit, and `sla_status` that `/attestations/held`, `/metrics`, and
  the CI gate use, so it cannot disagree with them about what is pending or
  breached. It ranks the record; it does not keep a second copy of it.
