# 0047 — CI Trust Gate

## Context

The platform can *report* its trust posture — `verify`, `/cvi`, `/status.json` —
but reporting is passive. A team adopting verification-as-a-service wants it to be
*enforcing*: fail the build, block the deploy, when trust regresses. The pieces
existed (an offline verifier that exits non-zero on a broken chain, a CVI, a
trustworthy flag) but nothing composed them into a single policy check a CI job
could call. `verify` alone is not enough — it catches a *broken* chain but passes
a ledger whose confidence has quietly collapsed or that was never sealed.

## Decision

Add a `gate` subcommand to the `oceanic_os.py` CLI — a composable trust gate.

- `python oceanic_os.py gate` reads the configured ledger and evaluates a policy,
  exiting `0` (pass) or `1` (fail) so it drops straight into any CI step.
- The policy is opt-in and additive: by default it requires only an intact chain
  (same floor as `verify`); `--require-trustworthy` additionally demands a valid
  signed checkpoint; `--min-cvi X` fails when the CVI is below a floor. Combine
  them for a strict gate.
- Released held items are credited to the CVI (via `HeldReviewLog`), so the gate's
  number matches what the service reports rather than a stricter shadow metric.
- It prints `PASS`/`FAIL` with the specific failing reasons (and `--json` for a
  structured report carrying the policy and reasons), so a red build says *why*.

## Consequences

- Verification becomes enforcing, not just observable: a build can now fail
  because trust *regressed*, not only because the chain broke. Verified live
  across four scenarios — a sealed high-CVI ledger passes the strict gate (exit
  0); a held entry dragging the CVI under the floor fails with `cvi 0.325 below
  floor 0.74` (exit 1); an intact-but-unsealed ledger fails `--require-trustworthy`
  with `not trustworthy` (exit 1) yet passes the default intact-only gate (exit 0).
- It is deliberately a *policy* layer over existing reads, distinct from `verify`
  (integrity alone). The gate composes `verify()` and `cvi()`; it computes no new
  trust fact, so it can never disagree with `/status.json` — it only decides
  whether the posture those report clears a bar.
- The CLI stays the single operator surface: `boot`/`verify`/`stats`/`ready` are
  the read tools, `gate` is the enforce tool, all reading the same configured
  `OCEANICOS_DB` with no service running. That makes the gate usable in a
  pre-deploy job or a cron integrity check, the same places the offline verifier
  already lives (`DECISIONS/0013`).
- Opt-in thresholds, not baked-in ones: a team picks its own CVI floor and whether
  a signature is mandatory, because the right bar is a deployment policy, not a
  property of the ledger. The default (intact-only) is the safe, non-surprising
  floor that matches `verify`.
