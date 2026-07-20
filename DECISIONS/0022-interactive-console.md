# 0022 — Full Interactive Verification Console

## Context

The web UI was a two-panel terminal (build + consensus). Meanwhile the API had
grown to cover the whole platform — CVI and chain integrity, signed checkpoints,
the searchable ledger, the held-review SLA queue, the explainable rules engine,
the 2019 anchor, Prometheus metrics, pricing, identity/observer. None of it was
reachable without curl. A platform you can only operate from the command line is
not the "fully interactive working app" the product implies.

## Decision

Rebuild `templates/index.html` into a single-page console that exercises every
subsystem against its live endpoint, keeping the terminal-nihilism aesthetic and
the deliberate 2500ms build friction.

- **Dashboard tiles** parse `/metrics` (public) for CVI, chain state,
  attestations, held pending, SLA breaches, panel size.
- **Panels**: identity/observer lineage; session identify (token stored for
  admin actions); build + attest (2500ms friction); the 4-member dissent panel
  rendering each verdict and the rules engine's reasons; explainable
  `/rules/evaluate`; parameterized ledger search; integrity (CVI, chain verify,
  admin checkpoint); the held-review queue with SLA aging and release/uphold
  buttons; the offline 2019 anchor lookup; live Prometheus text; pricing.
- Admin-gated calls (checkpoint, held-review) attach the token from the session
  panel; everything else is anonymous, matching each endpoint's own gate.

## Consequences

- The whole platform is now operable from the browser, and each control is a
  thin, honest client over the same endpoint the tests and CLI use — no bespoke
  UI backend, no divergent logic.
- Driving the console live caught a real bug that no unit test would: the build
  handler destructured `const { data }` from a helper that returned the result
  directly, so the attestation never rendered. Exercising the actual UI end to
  end — not just the API — is what surfaced it, and it was fixed before ship.
- Output is escaped before insertion (`esc()`), and the client holds no secret
  beyond the session token the user pastes; admin panels simply fail closed
  (403) without it, mirroring the server.
- The console is presentation only. It adds no endpoint and no state; if the API
  is the source of truth, the console is just its face, and it degrades to the
  same CSV/bundle/`/metrics` links when scripted access is preferred.
