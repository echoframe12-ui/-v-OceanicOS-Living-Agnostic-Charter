# 0064 — CVI Peak Observability

## Context

Round 63 (`DECISIONS/0063`) let the CI gate *enforce* a CVI regression — fail if
the index has fallen more than X below its recorded peak. But enforcement runs at
build time, on demand. Nothing *showed* the peak or the current gap the rest of
the time: an operator watching the status board saw the CVI but had no way to tell
whether `0.80` was this record's high-water mark or a slide down from `0.95`. The
regression baseline the gate used was invisible on the surfaces where trust is
watched continuously.

## Decision

Surface the CVI peak everywhere the CVI is already shown.

- `_status_snapshot` computes `cvi_peak` (the max of the recorded CVI history,
  defaulting to the current CVI when there is no history), so it flows to
  `/status.json` and the status board automatically.
- The board's CVI tile shows the gap when there is one — `▼0.15 from peak 0.95` —
  and `at peak` otherwise, so erosion reads at a glance in the same tile as the
  index.
- `/metrics` gains `oceanicos_cvi_peak`, a gauge beside `oceanicos_cvi`, so a
  monitor can alert on the current-vs-peak gap without running the gate.

## Consequences

- Regression is now visible, not only enforceable: verified live, a record at CVI
  `0.80` with a recorded peak of `0.95` shows `oceanicos_cvi_peak 0.95` on
  `/metrics`, `cvi_peak 0.95` on `/status.json`, and `▼0.15 from peak 0.95` on the
  board — the same slide the gate would fail on `--max-cvi-drop`, readable on every
  passive surface. Enforcement (round 63) and observation (this round) now share
  one baseline.
- The peak reads from the same `cvi_history` the gate uses, so the number the board
  shows and the number the gate measures against cannot diverge — one recorded
  trend, one peak, surfaced two ways.
- The default is honest for a fresh record: with no history the peak *is* the
  current CVI, so the tile reads `at peak` rather than inventing a gap — a record
  at its only known value has not regressed from anything.
- Presentation only — a derived read over the existing history, no new state. The
  board tile and the metric restate the trend; they do not compute a second peak
  that could disagree with the gate's.
