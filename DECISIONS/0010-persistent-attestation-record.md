# 0010 — Persistent Attestation Record

## Context

The attestation engine — the ledger of every verified output, and the source of
the Composite Verification Index — lived in a Python list on the engine
instance. Under a single worker that was fine. Under `gunicorn --workers 2`
(the production default) each worker held its own list: a build attested by
worker A was invisible to worker B, so `/cvi` returned a different value
depending on which worker answered the request. A worker that had handled no
builds reported `cvi 0.0` while its sibling reported the real score. The
verification record — the one thing this platform exists to keep — was the only
core state that wasn't shared.

Every other stateful surface (builds ledger, auth, usage audit, memory,
calendar, ground-truth cache) already persisted to the one SQLite database.
Attestations were the exception, purely for historical reasons.

## Decision

Persist attestations to the OceanicOS SQLite database, mirroring `UsageLog`.

- `AttestationEngine(db_path=None)` defaults to `OCEANICOS_DB` and creates an
  `attestations` table (`subject, actor, sha256, confidence, threshold, status,
  sources, created_at`). Sources are stored as a JSON array.
- `attest` inserts a row and returns the same dict shape as before; `id` is the
  row's autoincrement id. `list`, `held`, and `cvi` read from the table, scoped
  by actor exactly as before.
- Per-call connections (the `UsageLog` pattern), so concurrent workers reading
  and writing the shared file is SQLite's ordinary concurrency, not new
  machinery.
- `app.py` constructs the engine against `service.db_path`, the same file every
  other subsystem uses.

## Consequences

- `/cvi`, `/me/cvi`, `/admin/overview`, and `/attestations` are now consistent
  across workers: the CVI is the same number no matter which worker answers.
  The `--workers 1` caveat is gone.
- The verification record survives restarts, like every other ledger. The proof
  of what was verified is no longer the most volatile thing in the system.
- No API change. Every `attest/list/held/cvi` caller — the app, the universal
  builder, the tests — is untouched except for passing a db path.
- Node mounts and the model-router registry remain per-process; they are
  request-derived and hold no verification ground truth, so they carry no CVI
  correctness burden. If they ever need to be shared, this is the pattern.
