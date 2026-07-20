# 0009 — Windowed Rate-Limit Quotas

## Context

Round 11 enforced tier quotas as **lifetime** caps: an attestor who ran 10
builds ever was blocked forever unless an admin raised their tier. That is not
how a subscription meters — a tier should grant a rate (N builds per period),
resetting as time passes. The usage log (round 12) already timestamps every
build, so the rate window is a filter, not new state.

## Decision

Turn the lifetime ceiling into a **rolling window**.

- `quotas.WINDOW_SECONDS` (env `OCEANICOS_QUOTA_WINDOW`, default 3600) defines
  the period. The tier numbers are unchanged but now mean *builds per window*.
- `UsageLog.count_in_window(actor, action, window_seconds, now=None)` counts an
  actor's events of one action since `now - window`, and returns the oldest
  in-window timestamp. `now` is injectable so the window is testable without
  waiting.
- `/builder/run` and `/me/quota` meter against this windowed count.
  `resets_at = oldest_in_window + window` — the moment the oldest build ages out
  and a slot frees. A 429 carries `window_seconds` and `resets_at` so the client
  knows when to retry.

## Consequences

- Quotas are now genuinely subscription-shaped: usage recovers continuously
  instead of accumulating to a permanent wall.
- No new persistence — the window reads the existing usage-log timestamps, so
  the audit trail (round 12) and the rate limiter share one source of truth.
- The window is operator-tunable per deployment (`OCEANICOS_QUOTA_WINDOW`); the
  reference default is one hour.
- Backward compatible: `quota_status` keeps its round-11 keys and adds
  `window_seconds`/`resets_at`; `sovereign` stays unlimited.
