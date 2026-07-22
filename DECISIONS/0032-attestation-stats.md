# 0032 — Aggregate Attestation Statistics

## Context

The ledger could be searched (0021) and scored (the CVI is a single number), but
there was no at-a-glance view of the *shape* of the record: the confidence
distribution, the per-actor breakdown, the held ratio in context. Answering "what
does this verification record actually look like?" meant pulling the whole ledger
and computing client-side — work the server should do once.

## Decision

Add `AttestationEngine.stats(actor=None)` and `GET /attestations/stats`.

- `stats` reuses **the same scoped scan `cvi` uses** (`self.list(actor)`) and
  aggregates: `total` / `attested` / `held` / `held_ratio`; `mean` / `min` /
  `max` confidence; a `by_actor` count breakdown; and a quartile
  `confidence_buckets` histogram. An empty record returns a well-formed zeroed
  report, mirroring `cvi`'s empty-case contract.
- `GET /attestations/stats` (`?actor=`) exposes it — public and aggregate, like
  `/cvi` and `/attestations`.

## Consequences

- The record's shape is one request away: verified live — five attestations
  report the totals, a confidence histogram
  (`{0.00-0.25:1, 0.50-0.75:2, 0.75-1.00:2}`), a per-actor breakdown
  (`{alice:2, bob:2, carol:1}`), and a `held_ratio` of `0.6` that **matches
  `/cvi`'s exactly** — because both read the same scan.
- Consistency by construction is the point: sharing `list(actor)` with `cvi`
  means the stats and the trust index can never disagree about how much is held.
  A separate query path would risk exactly that drift.
- The quartile histogram is deliberately coarse and fixed (four buckets), so the
  distribution is legible at a glance and stable across deployments; the raw
  confidences remain available via `/attestations` search for anyone who needs
  finer granularity.
- Read-only, aggregate, and scope-aware — `?actor=` narrows both the counts and
  the `by_actor` map, keeping scoping the same consistent lens the rest of the
  API uses.
