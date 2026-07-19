# 0002 — Identity and Attribution

## Context

The platform's evolution report named authentication and multi-user support
as its next frontier. A living charter that says "humans remain accountable"
and "preserve provenance" needs to know *which* human stands behind each
action.

## Decision

Introduce token-based identity (`auth.py`, `AuthRegistry`) with two
properties:

1. **Attribution is always on.** Every request resolves to an actor — the
   authenticated username when a valid `Authorization: Bearer <token>` is
   present, otherwise `anonymous`. The actor is recorded in the build ledger
   (`builds.actor`) and in each attestation's source trail (`actor:<name>`),
   so provenance travels with the work.

2. **Enforcement is env-gated.** With `OCEANICOS_REQUIRE_AUTH=1` (surfaced as
   `app.config["REQUIRE_AUTH"]`), protected endpoints return `401` without a
   valid token. Default is open — development and the reference deployment
   stay frictionless, while a real deployment can lock the door.

Tokens are stored only as SHA-256 hashes and returned exactly once at
registration. No PII is required or kept — only a chosen username.

## Consequences

- Respect for dignity, privacy, and consent: no raw token or personal data is
  ever persisted or echoed.
- Charter alignment: accountability and provenance are now concrete, not
  aspirational.
- Trade-off: env-gated enforcement means the default posture is open. This
  matches the friction protocol's provenance-over-gatekeeping stance and keeps
  the reference implementation approachable; deployments that need a hard lock
  set one environment variable.
