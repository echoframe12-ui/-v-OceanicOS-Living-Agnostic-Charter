# 0052 — Gate: Held-Queue Health

## Context

The CI trust gate (`DECISIONS/0047`, `0048`) enforces the *record's* quality —
chain integrity, the signed seal, the CVI floor, source coverage. But a
verification platform also has an *operational* health that a purely record-based
gate ignores: the held queue. Held attestations are the ones below the confidence
threshold, waiting on a steward; a growing backlog, or items past their review
SLA, means trust decisions are being deferred, not made. A ledger can be intact,
sealed, confident, and well-sourced while a pile of unreviewed held items quietly
accumulates. The gate could not see that.

## Decision

Add the process dimension to the gate.

- `--max-held-pending N` fails the build when more than `N` held attestations
  await a steward decision (released items don't count, matching the CVI).
- `--no-sla-breach` fails when any pending held item is past the review SLA
  (`OCEANICOS_HELD_SLA_SECONDS`, default one day), computed with the same
  `sla_status` the service and `/metrics` use.
- The gate report and one-line summary now carry `held_pending` and
  `held_breached` beside the CVI and source coverage, so a red build shows the
  operational state whether or not it was the cause.

## Consequences

- The gate is now four-dimensional: record integrity (`intact`,
  `--require-trustworthy`), confidence (`--min-cvi`), evidence (`--min-sourced`),
  and *process* (`--max-held-pending`, `--no-sla-breach`) — a team can require
  that verification decisions are actually being made, not just that the settled
  record looks good. Verified live: three attestations with two held fail
  `--max-held-pending 1` with `held_pending 2 over limit 1` (exit 1) and pass
  `--max-held-pending 5` (exit 0).
- Held-queue health is computed exactly as the service computes it — the same
  `held()`, released-id credit, and `sla_status` — so the gate's `held_pending`
  and `held_breached` cannot disagree with `/metrics` or `/status.json`. The gate
  composes existing reads; it invents no operational metric of its own.
- Still opt-in: with neither flag the queue is only *reported*, never enforced, so
  the default gate is unchanged and a team adds the process bar deliberately. The
  SLA window is the deployment's existing `OCEANICOS_HELD_SLA_SECONDS`, not a new
  knob — the gate enforces the SLA the service already publishes.
- The two flags separate backlog *size* from backlog *age*: a team that tolerates
  a queue but not a stale one uses `--no-sla-breach` alone; one that caps depth
  uses `--max-held-pending`. Different operational policies, both expressible.
