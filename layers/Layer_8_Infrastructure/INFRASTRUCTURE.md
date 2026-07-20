# Layer 8: Infrastructure

What the platform runs on — and what it degrades to.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| WSGI entry point | `wsgi.py` | Any WSGI server can host the app |
| Process serving | `Procfile` | gunicorn with `PORT`-aware binding for Heroku-style platforms |
| Containerization | `Dockerfile` | Self-contained image, `python:3.12-slim` base |
| Continuous integration | `.github/workflows/ci.yml` | pytest on every push and PR, with isolated DB/workspace paths |
| Persistence | SQLite (`OCEANICOS_DB`) | Memory, plugins, builds ledger, usage audit, attestation record (the CVI source), calendar, and ground-truth cache in one file — so every worker reads the same verification state |
| Configuration | Environment variables | `HOST`, `PORT`, `OCEANICOS_DB`, `OCEANICOS_WORKSPACE`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `OCEANICOS_REQUIRE_AUTH`, `OCEANICOS_ADMIN_USERS`, `OCEANICOS_QUOTA_WINDOW`, `OCEANICOS_SIGNING_KEY` |
| Ledger integrity | `attestation_engine.verify()` / `checkpoint()` | Hash-chained attestations plus operator-signed checkpoints; `OCEANICOS_SIGNING_KEY` stays out of the database so a DB-only tamper can't forge a valid head |
| Graceful degradation | `/builds/export`, `/attestations/export` + `verify_ledger.py` | The builds ledger exports as CSV; the attestation ledger exports as a self-contained bundle that `verify_ledger.py` re-walks offline — the ground truth, and its integrity, survive without the system |

## Principles applied

- Resilience: one SQLite file and one CSV export stand between the platform and total loss.
- The cloud is a convenience, not a covenant: external API results are cached locally and served stale rather than failing.
