# 0045 — Machine-Readable Status Twin

## Context

Round 44 added `/status`, a human-facing trust board. But a monitor, a CI gate,
or an external dashboard cannot consume an HTML page — it would have to scrape
the markup or, worse, reassemble the posture itself from `/cvi`,
`/attestations/verify`, and `/attestations/audits` as three separate calls and
re-derive the `TRUSTWORTHY` / `INTACT` / `BROKEN` rollup by hand. The single
verdict the page computes existed only as rendered text, not as data anyone could
read. And a second surface computing the same posture independently is exactly
how two views drift apart.

## Decision

Extract the posture assembly into one helper and serve a JSON twin.

- `_status_snapshot()` computes the whole posture once — the `posture` verdict,
  the `verify` report, the CVI and its spread, the held queue and SLA breaches,
  the latest checkpoint and drift audit, the totals, the threshold, and a
  timestamp.
- `/status` now renders `status.html` from that snapshot; `/status.json` returns
  the same snapshot as JSON. A single source, so the human page and the machine
  twin can never disagree — verified live: both report `TRUSTWORTHY` for the same
  sealed record.
- `posture_class` (a CSS class name, purely presentational) is dropped from the
  JSON: the machine reads `posture`, the page reads the colour.

## Consequences

- The single posture verdict is now a first-class, consumable field. A monitor
  gets "is the verification layer healthy right now?" in one call with a
  three-state answer, instead of stitching it together from three endpoints and
  guessing the rollup rule — the rule now lives in exactly one place.
- HTML and JSON cannot drift, because they are the same dict rendered two ways.
  This is the DRY the console discipline (`DECISIONS/0034`) already implies,
  applied where it matters most: two representations of one truth.
- Still presentation only — `_status_snapshot` reads existing engine methods and
  adds no state. The twin exposes nothing `/status` did not already show; it
  changes the *format*, not the *surface area* (aggregate, public, no per-actor
  content), consistent with `/cvi` and `/metrics`.
- `/metrics` (Prometheus) and `/status.json` coexist by design: the former is a
  flat scalar exposition for a scraper's time-series, the latter a structured
  snapshot with the composite verdict and nested detail for a dashboard or a
  gate. Different consumers, same underlying reads.
