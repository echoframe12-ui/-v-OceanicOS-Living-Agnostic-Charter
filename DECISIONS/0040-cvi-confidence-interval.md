# 0040 — CVI Confidence Interval

## Context

The Observer's architecture tree lists "Confidence intervals" under Product, and
it was the last place the platform reported a point where it meant a range. The
CVI was a single number, and the terminal's own creed is "no false certainty" —
yet the trust index itself was stated as one figure with no sense of its spread.
A record of a hundred near-identical high confidences and a record split between
very high and very low can share a mean while meaning very different things; the
headline hid that.

## Decision

Report the CVI's underlying confidence as an interval.

- `AttestationEngine.cvi` now includes `confidence_interval: [low, high]` =
  `mean ± population standard deviation` of the confidence sample, clamped to
  `[0, 1]` and rounded. Every existing key is unchanged; the interval is
  additive.
- It is computed at query time from the same scan `cvi` already reads, so it
  agrees with `mean_confidence` by construction — no schema change, no new state.
- `/cvi`, `/me/cvi`, and the console's Integrity panel carry it with no further
  wiring, since they all render the `cvi()` dict.

## Consequences

- The trust index carries its own uncertainty: verified live — one sample yields
  a point `[0.9, 0.9]`, two spread samples (0.9, 0.5) yield `[0.5, 0.9]`
  (mean ± 0.2), and a wide mix yields `[0.02, 0.66]`. Wide when the record
  disagrees, a point when it's uniform — which is exactly the honest reading.
- The single-sample interval is deliberately zero-width: with one data point
  there is no spread to report, and inventing a band would be the false certainty
  this platform exists to refuse. The interval says "point" only when the data
  genuinely is one.
- Population (not sample) standard deviation is the right choice here: the CVI
  describes the record it has, not an inference about a larger population, so the
  spread is of the actual attestations, undivided by `n−1`.
- Non-invasive and consistent: because it is derived from the same confidences as
  the mean, the interval can never contradict the CVI it brackets, and it needed
  no migration — the record's shape is unchanged.
