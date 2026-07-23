# 0049 — Source Coverage Across the Observability Surfaces

## Context

Round 48 (`DECISIONS/0048`) added source coverage — `sourced_ratio`, the fraction
of the record that cites evidence — to `stats()` and made it enforceable in the CI
gate. But it was only *visible* on `/attestations/stats`. Every other place the
confidence axis is watched — the Prometheus scrape, the public status board, the
machine-readable status twin — was silent about evidence. A metric a monitor can't
scrape and a board can't show is measured but not observed: an operator would see
the CVI fall and have no matching signal for whether the record had also stopped
citing its sources.

## Decision

Propagate `sourced_ratio` to every surface that already carries the CVI.

- **`/metrics`** gains `oceanicos_sourced_ratio`, a gauge beside `oceanicos_cvi`,
  so a monitoring stack can alert on evidence coverage the same way it alerts on
  the trust index.
- **`_status_snapshot`** includes `sourced_ratio`, so it flows to `/status.json`
  automatically (the machine twin) and to the `/status` board.
- **The status board** gains a **Sourced** tile showing the coverage as a
  percentage, colour-banded on the same `0.74` threshold as the CVI tile — green
  at/above, amber below, red under `0.4` — so the evidence axis sits visibly next
  to the confidence axis it complements.

## Consequences

- Confidence and evidence are now watched side by side wherever trust is watched:
  verified live, a record of two sourced and one unsourced attestation reports
  `oceanicos_sourced_ratio 0.667` on `/metrics`, `sourced_ratio 0.667` on
  `/status.json`, and a `67%` amber tile on the board — the same number, three
  surfaces, no disagreement.
- This is pure propagation of the round-48 fact, not a new one: each surface reads
  the same `stats()["sourced_ratio"]`, so the metric, the twin, and the tile
  cannot drift from each other or from `/attestations/stats`. No new state, no
  schema change.
- The board's tile is banded on the confidence threshold deliberately, not on a
  separate evidence threshold: the platform holds one bar for "healthy", and
  showing evidence coverage against that same line keeps the board legible at a
  glance rather than introducing a second mental model. The gate remains the place
  to set a distinct, explicit `--min-sourced` policy when a team wants one.
- The observability trilogy (metrics, health, tracing) and the status surfaces now
  tell the whole trust story — integrity, seal, confidence, *and* evidence —
  through one consistent set of reads.
