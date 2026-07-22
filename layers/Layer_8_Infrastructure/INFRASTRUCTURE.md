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
| Configuration | Environment variables | `HOST`, `PORT`, `OCEANICOS_DB`, `OCEANICOS_WORKSPACE`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `OCEANICOS_REQUIRE_AUTH`, `OCEANICOS_ADMIN_USERS`, `OCEANICOS_QUOTA_WINDOW`, `OCEANICOS_SIGNING_KEY`, `OCEANICOS_CHECKPOINT_EVERY`, `OCEANICOS_HELD_SLA_SECONDS` |
| Ledger integrity | `attestation_engine.verify()` / `checkpoint()` | Hash-chained attestations plus operator-signed checkpoints; `OCEANICOS_SIGNING_KEY` stays out of the database so a DB-only tamper can't forge a valid head. `OCEANICOS_CHECKPOINT_EVERY` auto-seals the head on a cadence so the signed guarantee runs without a human in the loop |
| Graceful degradation | `/builds/export`, `/attestations/export` + `verify_ledger.py`, `/anchor` + `anchor.py` | The builds ledger exports as CSV; the attestation ledger exports as a self-contained bundle that `verify_ledger.py` re-walks offline; past both sits the Anchor of Last Resort (`boot/anchor_2019.txt`) — a fixed 2019 dataset that `anchor.py` answers from with nothing else running. The ground truth, and its integrity, survive without the system |
| Boot | `oceanic_os.py` + `boot/init.v1` | `oceanic-os --boot boot/init.v1 --state stateless --exit 0` instantiates the stack from the ratified, hash-attested manifest and reports the live status of each layer |
| Observability | `metrics.py` + `/metrics` | Platform state (CVI, held queue, SLA breaches, chain integrity, builds, adapters) in the Prometheus text exposition format — scrapeable by any monitoring stack, no custom integration |
| Liveness & readiness | `/health`, `readiness.py` + `/readyz` | `/health` is liveness (process up); `/readyz` probes the real dependencies (database reachable, workspace writable) and returns 503 when one is down, so an orchestrator gates traffic correctly; see [DECISIONS/0026](../../DECISIONS/0026-readiness-probe.md) |
| Config introspection | `/config` (admin) | Reports the effective runtime config (auth mode, quota window + tiers, held SLA, checkpoint policy, whether signing is enabled) from the live objects — never a secret value; see [DECISIONS/0027](../../DECISIONS/0027-config-introspection.md) |

## Principles applied

- Resilience: one SQLite file and one CSV export stand between the platform and total loss.
- The cloud is a convenience, not a covenant: external API results are cached locally and served stale rather than failing.
