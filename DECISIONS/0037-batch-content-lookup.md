# 0037 — Batch Content-Addressable Lookup

## Context

Round 41 (DECISIONS/0035) added single content lookup: hold one output, ask
whether it was attested. But a real caller often holds a *set* — a page of
generated results, a batch of decisions, a document's worth of claims — and
verifying them one HTTP round-trip at a time is needless overhead. The reverse
lookup existed; it just didn't scale to a working set.

## Decision

Add `POST /attestations/lookup/batch`.

- The body carries `contents` (each hashed server-side with the same SHA-256) and
  /or `sha256s` (used directly), both lists. The response is
  `{count, results}` with one `{sha256, found, matches}` per item, **in order**,
  so a caller can line results back up with its inputs positionally.
- The batch is capped at 100 items; a larger batch, or a body with neither list,
  is a `400`.

## Consequences

- A working set is verified in one call: verified live — `["Report A", "Report B
  (fabricated)", "Report C"]` returns `found: [true, false, true]` in order,
  over the cap returns `400`, and a body with neither list returns `400`.
- It is the single-lookup primitive applied per item — the same
  `by_content_hash` and the same server-side hashing — so a batch result and the
  equivalent single lookups are identical by construction; the batch endpoint
  adds no new verification logic, only iteration and a bound.
- The cap is a deliberate, explicit limit (100), not an accident of
  implementation: it bounds the work a single request can demand without a
  per-actor scheme, keeping the public endpoint cheap to expose. A caller with
  more than 100 items pages.
- Order preservation is part of the contract: results map to inputs by position,
  so the caller needs no echo of its own content and no secondary join — the
  index is the key.
