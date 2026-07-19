# 0008 — Consensus-Weighted Confidence

## Context

The dissent panel (0007) and the attestation confidence score (0005-era
friction protocol) both existed, but they ran in parallel: the panel produced
a verdict split that nobody consumed, and confidence was purely an
evidence-count. The friction protocol's whole point — surface disagreement
into the decision — was only half-wired.

## Decision

Fold the panel's verdicts into the confidence that governs the 0.74 hold line.

- Each builder run now convenes the dissent panel on its task (`route_all`,
  panel of 3) and derives a `consensus_delta` from the verdicts:
  - unanimous `approve` → **+0.10**
  - unanimous `revise` → **−0.20**
  - split → **±0.05 / ±0.10** by majority
  - abstentions → **0.0** (a panel with no opinion moves nothing)
- `score_confidence(evidence, context_provided, consensus=delta)` applies the
  delta and clamps to [0, 0.99].
- The consensus (verdicts, distribution, majority, dissent) is recorded in the
  attestation source trail (`consensus:<majority>(dissent|agreement)`) and
  returned on the run result.

## Consequences

- The panel now **moves the hold decision**: a unanimous "revise" pulls even a
  fully-evidenced build below the threshold and holds it for a human; a
  unanimous "approve" can rescue an under-evidenced (context-free) build.
- "Certainty is a bug" becomes operative — disagreement lowers confidence
  rather than sitting beside it in a separate endpoint.
- The evidence-count remains the base; consensus is a bounded nudge, never a
  a veto — a strong build with a split panel still stands, a weak one with
  unanimous doubt is held.
- Backward compatible: `consensus` defaults to 0.0, and a router with no
  verdict strategies abstains, so existing single-adapter builders are
  unchanged.
