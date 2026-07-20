# 0023 — CVI Trend History

## Context

The Composite Verification Index is the platform's headline trust signal, but
`/cvi` and `/metrics` only ever report the current value. A trust index with no
memory can't answer the question it exists for: is verification quality
improving or slipping? The number was live but historyless.

## Decision

Record the CVI over time and expose the trend.

- `cvi_history.py` (`CviHistory`, mirroring `usage.py`) persists snapshots to a
  `cvi_snapshots` table, per actor (`''` = the platform-wide series).
- Recording is **change-only**: `record_if_changed` writes a point only when the
  `cvi` or `samples` differs from the latest one for that series. Reading the CVI
  a hundred times without a build in between adds no rows; the series is a trend
  of real movement, and its growth is bounded by how often quality actually
  changed — not by traffic.
- Snapshots are taken at the two points the CVI can move: after a successful
  build (`/builder/run`) and after a held-review decision
  (`review_held_attestation`, since a release lifts the held ratio). The helper
  `_snapshot_cvi()` computes the current platform CVI with released items
  credited and calls `record_if_changed`.
- `GET /cvi/history` (`?actor=`, `?limit=`) returns the series oldest→newest —
  public and aggregate, consistent with `/cvi`. The console draws a compact
  unicode sparkline from it in the Integrity panel.

## Consequences

- The CVI becomes a watchable signal: a live series whose latest point always
  equals `GET /cvi`, extending as builds land and shifting when a steward
  releases a held item. Verified live and in the console sparkline.
- Change-only recording is the deliberate trade: the series captures every real
  move but is not a per-request time series, so it stays small without a
  retention job. If a fixed-cadence sample is ever wanted (e.g. hourly for a
  dashboard), it is an additional caller of `record`, not a change to the store.
- Scoped by actor from the start (`''` platform, or a username), so a per-actor
  trust trend is available without a schema change — the `/me/*` surface can
  adopt it when needed.
- History is derived, not authoritative: it records what the CVI *was*, computed
  from the immutable ledger. It adds no ledger state and cannot alter the chain;
  losing it costs the trend, never the ground truth.
