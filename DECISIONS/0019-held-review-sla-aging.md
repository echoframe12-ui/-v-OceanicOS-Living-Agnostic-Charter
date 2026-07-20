# 0019 — Held-Review SLA Aging

## Context

Round 18 (DECISIONS/0018) built the held-review workflow — a steward can release
or uphold a held attestation — and called it the Arbiter tier's "held-review
SLA." But an SLA is a promise about *time*, and there was none: a held item
showed `pending` with no sense of how long it had waited or whether the promise
was being kept. "SLA" was a workflow, not a service level.

## Decision

Age held attestations against a configurable time-to-decision SLA.

- `held_reviews.sla_status(held_created_at, latest_review, sla_seconds, now=None)`
  is a pure function over timestamps already on record. A held item is `pending`
  until reviewed — reporting `age_seconds` and `sla_breached` once its age
  exceeds the SLA — then `decided`, reporting `decision_seconds` and whether the
  decision landed `within_sla`. The SLA measures time to a *decision*, not to a
  release: an uphold satisfies it as much as a release, because the steward
  answered. `now` is injectable, so aging is tested without waiting.
- `OCEANICOS_HELD_SLA_SECONDS` (default 86400 — 24h) sets the window; `0`
  disables breach flags entirely.
- `GET /attestations/held` annotates each item with its `sla` block;
  `/admin/overview` reports `held_sla_breached` (pending items past the window)
  and `held_sla_seconds`.

## Consequences

- The advertised SLA is now measurable and enforced in the open: a steward and
  an auditor can both see which held items are breaching and how long decisions
  took. Verified live — a pending item flips to `sla_breached: true` once its age
  passes a 2s test window, `/admin/overview` counts the breach, and a later
  uphold records `within_sla: false` with the elapsed `decision_seconds`.
- It is pure presentation over existing data. The SLA reads the attestation's
  `created_at` and the review's `created_at`; it stores nothing new and changes
  no ledger state, so it can be tuned or disabled per deployment without a
  migration and without touching the chain.
- Time to *decision*, not to *release*, is the honest metric: the platform
  controls when it reviews, not what the evidence says. Holding an item after
  review is a valid, SLA-satisfying outcome; the promise is a timely answer, not
  a guaranteed release.
- `sla_seconds = 0` is a first-class "no SLA" mode, so a deployment that doesn't
  sell the SLA carries no false breach signal.
