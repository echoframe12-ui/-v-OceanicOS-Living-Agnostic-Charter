# 0005 — Per-Tier Build Quotas

## Context

Round 7 shipped VaaS pricing tiers (Attestor / Arbiter / Sovereign) as prices
with nothing behind them, and round 10 gave admins the authority to govern.
The friction protocol's mantra — "charge a premium for the humanosecond it
takes to squint at the output" — stays hollow until a tier actually buys
something. This round makes tiers enforceable.

## Decision

Map each tier to a build ceiling (`quotas.py`):

| Tier | Build limit |
| --- | --- |
| Attestor | 10 |
| Arbiter | 50 |
| Sovereign | unlimited |

- New users default to **attestor**. Only an **admin** can change a tier
  (`POST /admin/users/<username>/tier`) — a user cannot upgrade itself, the
  same appointment principle as the admin role (decision 0004).
- `/builder/run` meters **named actors** against their tier and returns **429**
  with a structured `{error, tier, limit, used}` when the ceiling is reached.
- **Anonymous is unmetered.** In the open reference deployment the anonymous
  path is the free, ungoverned lane; under `OCEANICOS_REQUIRE_AUTH=1` there is
  no anonymous actor, so every request is a named, metered account.
- `GET /me/quota` reports `{tier, limit, used, remaining, exceeded}` so a user
  can always see where they stand.

## Consequences

- The pricing tiers are now load-bearing, not decorative — the premium buys a
  real ceiling.
- Enforcement is honest about who pays: named accounts are metered by tier,
  and the assignment authority stays with appointed admins.
- Backward compatible — the limit lookup and the tier column both default to
  attestor, and anonymous open-mode use is unchanged.
