# 0048 — Source Coverage

## Context

The platform's founding creed is *attest, don't assert*: an output should carry a
content hash, a confidence, **and a source trail**. Every attestation already
stores its `sources`, and the confidence side is measured everywhere (the CVI,
its interval, the histogram). But the *evidence* side was never surfaced. Nothing
reported how much of the record actually cites a source — and a high-confidence
attestation with an empty source list is a distinct trust smell the CVI cannot
see: confidence and evidence are different axes, and only one of them was visible.

## Decision

Measure evidence coverage and make it enforceable.

- `AttestationEngine.stats()` gains `sourced` (attestations with at least one
  source) and `sourced_ratio` (its fraction of the total), computed from the same
  scoped scan as every other stat, so it agrees with them by construction. The
  empty-record case returns `0` / `0.0`, mirroring the existing zeroed contract.
- `/attestations/stats` carries the fields automatically (it returns `stats()`).
- The CI gate (`DECISIONS/0047`) gains `--min-sourced X`, failing the build when
  coverage drops below a floor — evidence discipline enforced the same way the
  CVI floor and the trustworthy requirement already are.

## Consequences

- The creed is now measurable and enforceable, not just aspirational: verified
  live, a record of three sourced and one unsourced attestation reports
  `sourced_ratio 0.75`, the gate fails `--min-sourced 0.9` with `sourced_ratio
  0.75 below floor 0.9`, passes `--min-sourced 0.7`, and composes with
  `--min-cvi` in one strict gate.
- Source coverage is deliberately a *second axis* beside confidence. A record can
  be highly confident and poorly evidenced, or well-evidenced and appropriately
  uncertain; collapsing them into one number would hide exactly the distinction
  the platform exists to make. The gate can now demand both.
- Presentation of an existing fact, not a new one: `sources` was always stored;
  this counts it. No schema change, no migration, and — because it reads the same
  scan as the rest of `stats()` — it cannot disagree with the totals it sits
  beside.
- Coverage measures *presence* of evidence, not its quality — one source counts
  the same as ten. That is the honest floor: the platform can assert an
  attestation cites *something*, but judging whether the something is good is the
  dissent panel's and a steward's job, not a ratio's.
