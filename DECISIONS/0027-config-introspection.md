# 0027 — Operational Config Introspection

## Context

The platform's behavior is shaped by a spread of environment variables
(`OCEANICOS_REQUIRE_AUTH`, `OCEANICOS_QUOTA_WINDOW`, `OCEANICOS_HELD_SLA_SECONDS`,
`OCEANICOS_SIGNING_KEY`, `OCEANICOS_CHECKPOINT_EVERY`, `OCEANICOS_ADMIN_USERS`),
but a running instance offered no way to answer "what configuration are you
actually using?" Debugging a misbehaving deployment meant shelling in to read env
and hoping the process picked up what was set. The observability trilogy —
metrics (0020) and readiness (0026) — was missing its third leg: the config an
operator can inspect.

## Decision

Add `GET /config` (admin-gated), reporting the effective runtime configuration.

- `_effective_config()` reads from the **live objects**, not raw env: auth mode
  from `app.config`, the quota window and tier limits from `quotas`, the held
  SLA, the checkpoint policy and adapter list from the engine and router, the
  effective db and workspace paths. It reports the truth the process is running,
  not the intent someone set — the two can differ (a typo'd env var, a default
  that kicked in), and the difference is exactly what a config probe exists to
  reveal.
- **No secret is ever assembled into the response.** Signing is reported as the
  boolean `signing_enabled`, sourced from `attestation_engine.can_sign` — the key
  stays inside the engine and is never read by the handler. No token appears. A
  test asserts the configured key string is absent from the entire serialized
  response.
- Admin-gated (`require_admin`): the effective config is operator information, a
  stewardship view like `/admin/overview`, not a public read.

## Consequences

- An operator can confirm what an instance is running without shell access:
  verified — with a key set, `/config` reports `signing_enabled: true`, and the
  key value appears nowhere in the response. A non-admin gets 403.
- Reporting *enabled* without the secret is the whole point, and it falls out of
  the design rather than being bolted on: the engine already exposed `can_sign`
  as a boolean (rounds 18/20), so the config surface can prove the feature is on
  without the handler ever touching the key. New config that involves a secret
  must follow the same rule — report a derived boolean, never the value.
- Reading from live objects means the endpoint can't drift from behavior: the
  same `quotas.WINDOW_SECONDS` and `attestation_engine.checkpoint_policy` that
  govern requests are what `/config` reports. One source, two uses.
