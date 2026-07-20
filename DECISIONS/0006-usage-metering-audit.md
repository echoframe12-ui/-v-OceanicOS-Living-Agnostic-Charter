# 0006 — Usage Metering & Audit Trail

## Context

Round 11 made tiers enforceable, but enforcement without a record is opaque:
a 429 tells a user "no" without telling anyone "why" or "how often." Quotas
that bill for the humanosecond need an auditable history — what was spent, by
whom, at what tier, and when a limit bit.

## Decision

Add a persistent usage log (`usage.py`, SQLite in the OceanicOS database):

- Every metered event is recorded with `actor`, `action`, the `tier` in force,
  a `detail`, and a timestamp. Actions logged today:
  - `build` — a successful builder run
  - `quota_exceeded` — a run refused because the tier ceiling was reached
  - `tier_change` — an admin reassigned a tier (detail records who)
- **Scoped self-view:** `GET /me/usage` returns only the caller's own events.
- **Steward view:** `GET /admin/usage` (admin-only, optional `?actor=`) returns
  the full trail; `/admin/overview` gains a per-action usage rollup.

The log is append-only in practice and survives restarts, so it is a genuine
audit surface, not a running counter.

## Consequences

- Quotas become auditable and, in principle, billable — the usage log is the
  history a tier's price is charged against.
- Preserve provenance and history (a charter principle) now extends past the
  build ledger to every metered decision, including the refusals.
- Same scoping discipline as the rest of the platform: members see their own
  usage; only an appointed steward sees across actors, and even then the log is
  event metadata, not the content of anyone's work.
