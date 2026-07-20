# 0021 — Parameterized Attestation Search

## Context

`GET /attestations` returned everything, filterable only by `?actor=`. That was
fine for a demo record, but the ledger is designed to grow — every build, every
review, every checkpoint adds to it — and a growing record you can only dump in
full is a record you can't actually use. A steward looking for held items, or a
CVI investigation into low-confidence attestations in a time window, had to pull
the whole ledger and filter client-side.

## Decision

Add server-side, fully parameterized filtering to the record.

- `AttestationEngine.search(*, actor, status, min_confidence, max_confidence,
  subject_contains, since, limit)` builds a SQL `WHERE` from only the supplied
  filters, each as a **bound parameter** — never string-interpolated. Filters
  compose with `AND`; confidence bounds and `since` are inclusive; no filters
  returns the whole record in order, identical to `list()`.
- `GET /attestations` accepts the matching query params (`status`,
  `min_confidence`, `max_confidence`, `subject`, `since`, `limit`, plus the
  existing `actor`), validates them (`status` in `{attested, held}`; numeric
  bounds and integer `limit` or `400`), and returns the filtered set. No params
  preserves the old behavior exactly, so existing callers are unaffected.
- The row→dict mapping was extracted into `_to_dict`, shared by `_rows` and
  `search`, so the two read paths cannot drift.

## Consequences

- The record is queryable as it scales: held items, a confidence band, a subject
  substring, a time window, a capped page — server-side, without shipping the
  whole ledger. Verified live: `?status=held`, `?actor=alice&min_confidence=0.92`,
  `?subject=charter`, and `?limit=1` each return exactly the expected rows.
- Injection is closed by construction, not by escaping. Every filter is a bound
  parameter, so a payload like `'; DROP TABLE attestations;--` in `subject` is
  matched as a literal string (zero results) and the table is untouched —
  confirmed by a live request and a test. New filters extend the same
  parameterized pattern; there is no interpolation seam to widen.
- Read-only and non-breaking: search touches no state, changes no chain, and the
  default (no filters) is byte-for-byte the previous response. It is a lens over
  the record, consistent with the platform's stance that scoping is a view and
  the ledger itself is immutable.
