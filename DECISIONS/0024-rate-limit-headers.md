# 0024 — Standard Rate-Limit Headers

## Context

The quota system (DECISIONS/0009) meters builds per tier over a rolling window
and returns `429` when a named actor exceeds its rate — with the numbers in the
JSON body. But HTTP clients, proxies, and SDKs discover rate limits through
*headers*, not by parsing a body: `X-RateLimit-Limit`, `-Remaining`, `-Reset`,
and `Retry-After` on the `429`. Without them, a well-behaved client can't back
off correctly, and the metered endpoints don't speak the ecosystem's language.

## Decision

Emit standard rate-limit headers alongside the existing JSON.

- `_rate_limit_headers(status)` derives them from a `quota_status` dict:
  `X-RateLimit-Limit` and `X-RateLimit-Remaining` for finite tiers,
  `X-RateLimit-Reset` as a unix timestamp once the window has an oldest build to
  age out, and `Retry-After` (seconds) on an exceeded quota.
- `/builder/run` attaches them on both paths: on the `429`, and on a successful
  build — recomputing the quota *after* the build so `Remaining` reflects the
  slot just consumed. `/me/quota` carries them too.
- Unlimited tiers (sovereign) emit **no** rate-limit headers: there is no ceiling
  to advertise, and a fabricated one would be misleading.
- The anonymous open path stays unmetered and header-free, matching its quota
  exemption.

## Consequences

- Metered endpoints are now client-friendly by the common convention: an SDK
  reads `X-RateLimit-Remaining` to pace itself and honors `Retry-After` on a
  block, with no body parsing. Verified live — a successful attestor build
  returns `Limit: 10, Remaining: 9, Reset: <ts>`, and a blocked build returns
  `429` with `Remaining: 0, Retry-After: 3599`.
- The headers are a second view of the same source of truth (`quota_status`),
  not a parallel counter, so they can never disagree with the JSON body or
  `/me/quota`. One computation, two representations.
- Reset is a unix timestamp (seconds), the widely-supported form; `Retry-After`
  is the relative seconds the spec prefers for a `429`. Emitting `Reset` only
  once there is an oldest in-window build avoids inventing a reset time for an
  actor who has used nothing.
- Purely additive: no request changes, the JSON bodies are untouched, and
  unlimited tiers and anonymous callers see exactly what they did before.
