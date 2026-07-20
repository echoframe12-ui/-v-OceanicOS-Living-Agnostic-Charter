# 0026 — Readiness Probe

## Context

The platform ships a `Dockerfile`, a `Procfile`, and a `/health` endpoint — but
`/health` is a *liveness* signal: it says the process is up, nothing more. A
container orchestrator needs a second, distinct signal to decide when an instance
should receive traffic: is it actually *able* to serve? A live process whose
database is unreachable or whose workspace is unwritable will fail every real
request while happily reporting healthy. That is exactly the gap a readiness probe
closes, and the deployable story wasn't complete without it.

## Decision

Add `GET /readyz`, a readiness probe over the real dependencies.

- `readiness.py` provides pure checks: `check_db` (the SQLite database answers a
  trivial query) and `check_workspace` (the artifact directory exists — creating
  it if missing — and is writable). `probe(db_path, workspace)` runs them and
  reports `{ready, checks}`, where `ready` is the AND of the operational
  dependencies.
- `/readyz` returns the probe plus `chain_intact` as informational context, with
  HTTP **200** when ready and **503** when a dependency is down — the status code
  an orchestrator gates on.

## Consequences

- Liveness and readiness are now separate signals, as they should be: `/health`
  for "restart me if I'm dead," `/readyz` for "route to me only when I can
  serve." Verified live — a healthy instance returns `200 {ready: true}`, and one
  pointed at an uncreatable workspace returns `503 {ready: false, checks:
  {workspace: false}}`, which pulls it from rotation until it recovers.
- Readiness gates on the *operational* dependencies (db, workspace), not on
  integrity: a broken hash chain is a grave problem, but the instance can still
  serve traffic, so `chain_intact` is reported as context rather than forcing a
  503. Conflating "can serve" with "is trustworthy" would take a servable node
  out of rotation for a problem that pulling it can't fix. The distinction is
  deliberate and documented, and a deployment that wants stricter gating can add
  `chain_intact` to the `ready` computation in one place.
- The checks are pure and take paths, not the app, so they are unit-tested in
  isolation and reusable by the boot CLI or any other caller. No new dependency —
  just `sqlite3` and `os`.
