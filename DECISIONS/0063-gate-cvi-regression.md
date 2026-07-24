# 0063 — Gate: CVI Regression Detection

## Context

The CI trust gate (`DECISIONS/0047`) enforces *absolute* thresholds — a CVI floor,
a source-coverage floor, held-queue limits. But an absolute floor cannot see a
*regression*: a record whose CVI slips from `0.95` to `0.80` has lost real trust,
yet still clears a `0.74` floor and passes the gate. The platform records the CVI
over time (`cvi_history`, `DECISIONS/0023`), so the trend was available — but the
gate ignored it. A build could keep passing while trust quietly eroded, so long as
it never fell all the way to the floor.

## Decision

Add `--max-cvi-drop X` to the gate — a relative check against the recorded peak.

- The gate reads the platform-wide CVI history and takes its **peak** as the
  baseline. If the current CVI has fallen more than `X` below that peak, the gate
  fails, reporting the drop, the peak, and the limit.
- With no recorded history there is no baseline, so the check is a no-op that
  passes — a regression cannot be asserted against a peak that does not exist.
- The report carries `cvi_peak` and the `max_cvi_drop` policy alongside the
  existing fields, so a red build shows the baseline it was measured against.

## Consequences

- The gate now catches erosion, not only violation: verified live, a record at CVI
  `0.80` **passes** `--min-cvi 0.74` (it clears the floor) but **fails**
  `--max-cvi-drop 0.1` with `cvi 0.8 dropped 0.15 below peak 0.95` — the two checks
  are complementary, one guarding the absolute bar and the other the trajectory.
- Peak, not last-point, is the deliberate baseline: measuring against the highest
  CVI the record ever reached asks "have we lost ground from our best?", which is
  the regression a team actually cares about, and it is monotonic — a single bad
  build cannot lower the bar it will later be judged against.
- Composition over new state: the peak is read from the same `cvi_history` the
  service records and `/cvi/history` serves, so the gate's baseline cannot disagree
  with the trend the platform reports, and no new storage was added.
- Opt-in and history-dependent by design: the check does nothing without a floor
  set *and* a recorded history, so the default gate is unchanged and a fresh
  deployment with no trend is never failed for a regression it has no basis to
  claim.
