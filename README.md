# Ω∞v OceanicOS Living Agnostic Charter

![OceanicOS — Living Agnostic Charter](static/brand/oceanicos-badge.png)

This repository is the starting point for a living, agnostic charter for OceanicOS: a flexible framework for building open, resilient, and human-centered systems without locking the project into rigid assumptions.

## Status: Activated

The repository is now initialized with a constitutional framework, a practical platform foundation, and a runnable prototype for an open orchestration layer.

## Purpose

The purpose of this charter is to define the values, principles, and working habits that guide the project over time. It should remain adaptable, clear, and useful as the project evolves.

## Core Principles

Every implementation and task execution within this framework should uphold:

1. Reality before assumption.
2. Evidence before conclusion.
3. Truth before convenience.
4. Humans remain accountable.
5. Respect dignity, privacy, and consent.
6. Explain significant reasoning where appropriate.
7. Preserve provenance and history.
8. Design for interoperability.
9. Learn continuously.
10. Steward for future generations.

The practical project principles are also expressed as:

- Openness: make decisions, processes, and knowledge understandable and shareable.
- Interoperability: favor systems and practices that work well across contexts and communities.
- Human agency: keep people, dignity, and consent at the center of design and governance.
- Resilience: build for continuity, recovery, and long-term sustainability.
- Inclusivity: welcome diverse perspectives and reduce unnecessary barriers to participation.

## Constitution and Platform Foundations

OceanicOS is not intended to become a single chatbot. It is intended to become an open orchestration layer that can:

- preserve memory across work and sessions
- plan and explain its reasoning
- coordinate tools such as GitHub, calendars, files, and external services
- work with multiple models and providers
- remain transparent, auditable, and adaptable

The foundational documents are:

- [CONSTITUTION.md](CONSTITUTION.md) for the operating principles and governance rules
- [ARCHITECTURE.md](ARCHITECTURE.md) for the system layers and execution model
- [MEMORY.md](MEMORY.md) for the persistent memory approach
- [GOVERNANCE.md](GOVERNANCE.md) for the stewardship and review model
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the first practical build phases
- [API_SPEC.md](API_SPEC.md) for the initial orchestration API and plugin model
- [DIAGRAM.md](DIAGRAM.md) for the architecture overview
- [OPEN_ORCHESTRATION_SPEC.md](OPEN_ORCHESTRATION_SPEC.md) for the consolidated platform specification
- [ROADMAP.md](ROADMAP.md) for the implementation milestones

## Platform Direction

OceanicOS is now structured as an open orchestration layer with a foundation for:

- planning and reasoning
- persistent memory
- workflow execution
- tool integration
- model routing
- observable agent events

The consolidated spec is available in [OPEN_ORCHESTRATION_SPEC.md](OPEN_ORCHESTRATION_SPEC.md).

## Starter Implementation

A minimal starter service is now included in [server.py](server.py), with a Flask-based HTTP interface in [app.py](app.py), a runnable demo in [main.py](main.py), and a browser-based builder entry point in [templates/index.html](templates/index.html). It demonstrates:

- a health endpoint
- plan creation
- persistent memory storage and lookup via SQLite
- a small tool registry with an echo tool
- a simple plugin registration model for future integrations
- a workflow engine for creating and executing multi-step plans
- an interactive builder experience that runs planning, routing, review, and artifact creation

Run the demo with:

```bash
python main.py
```

Run the Flask app with:

```bash
python app.py
```

Then open the starter UI at http://127.0.0.1:5000/.

Use the endpoints:

- GET /health
- GET /readyz
- GET /config
- GET /openapi.json
- POST /plans
- POST /memory
- GET /memory?query=review
- GET /tools
- POST /tools/echo
- POST /workflows
- GET /workflows/<name>
- POST /workflows/<name>/execute
- POST /plans/execute
- GET /plans/trace
- GET /models
- POST /models/route
- POST /models/consensus
- POST /rules/evaluate
- GET /builds
- GET /builds/export
- GET /builds/export.txt
- GET /attestations
- GET /attestations/stats
- GET /attestations/held
- POST /attestations/<id>/review
- GET /attestations/<id>/reviews
- GET /attestations/<id>/receipt
- GET /attestations/verify
- POST /attestations/verify-bundle
- POST /attestations/checkpoint
- GET /attestations/export
- GET /cvi
- GET /cvi/history
- GET /metrics
- POST /nodes
- GET /nodes
- GET /pricing
- GET /observer
- GET /anchor
- GET /adr
- GET /adr/<number>
- POST /auth/register
- GET /auth/whoami
- GET /auth/users
- GET /me/builds
- GET /me/attestations
- GET /me/memory
- GET /me/cvi
- GET /me/cvi/history
- GET /me/quota
- GET /me/usage
- GET /admin/overview
- GET /admin/users
- POST /admin/users/<username>/tier
- GET /admin/usage
- POST /agent/run
- GET /agent/events
- POST /state
- GET /state
- POST /reviews
- POST /reviews/<proposal>/approve
- GET /reviews
- POST /decisions
- GET /decisions
- POST /artifacts
- GET /artifacts
- POST /dashboard
- GET /dashboard
- POST /plugins
- GET /plugins
- POST /builder/run
- GET /builder/history
- POST /builder/evolve

Run the universal builder with:

```bash
python universal_builder.py
```

Run the test suite with:

```bash
python -m pytest -q
```

You can also configure host, port, and debug settings with environment variables:

```bash
HOST=127.0.0.1 PORT=9000 FLASK_DEBUG=0 python app.py
```

> Reality is the source. Evidence guides understanding. Humans lead. OceanicOS connects. Better reality is the outcome.

## Deployment

The app ships as a full-stack deployable service:

- [wsgi.py](wsgi.py) exposes the Flask app for any WSGI server
- [Procfile](Procfile) runs the app under gunicorn for Heroku-style platforms
- [Dockerfile](Dockerfile) builds a self-contained container image

Run in production mode locally:

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

Or with Docker:

```bash
docker build -t oceanicos .
docker run -p 5000:5000 oceanicos
```

The SQLite database location can be configured with the `OCEANICOS_DB` environment variable (defaults to `oceanicos.db` in the working directory).

There is also a `Makefile` for one-command full-stack builds:

```bash
make test           # run the suite
make stack          # test -> docker build (the whole stack)
make docker-run     # run the container
```

> **Worker note:** SQLite-backed state — builds ledger, auth/users, usage audit, memory, calendar, ground-truth cache, and the attestation record (and therefore `/cvi`) — is shared across gunicorn workers, so the CVI reads the same from every worker (see [DECISIONS/0010](DECISIONS/0010-persistent-attestation-record.md)). What remains per process is request-derived and holds no verification ground truth: node mounts and the model-router registry. Multi-worker deployment needs no special flags.

## Real Model Provider

When the `ANTHROPIC_API_KEY` environment variable is set, the app registers a `claude` adapter ([claude_adapter.py](claude_adapter.py)) that routes prompts mentioning "claude" to a real Claude model (`claude-opus-4-8`) through the official Anthropic SDK:

```bash
ANTHROPIC_API_KEY=sk-ant-... python app.py
curl -X POST http://127.0.0.1:5000/models/route -H 'Content-Type: application/json' -d '{"prompt": "Ask claude to summarize the charter principles"}'
```

Without the key, the app runs fully offline on the demo adapters.

## Tool Plugins

The tool registry ships with plugins beyond the built-in `echo`, `timestamp`, and `word_count` tools ([tool_plugins.py](tool_plugins.py)):

- `file_list`, `file_read`, `file_write` — file operations sandboxed to the workspace directory (`OCEANICOS_WORKSPACE`, default `workspace/`); paths that escape the sandbox are rejected
- `calendar_add`, `calendar_list` — calendar events persisted to the OceanicOS SQLite database
- `github_repo_info`, `github_issues` — read-only GitHub API tools (set `GITHUB_TOKEN` for private repos and higher rate limits). Successful responses are cached in a SQLite `ground_truth` table; when the network is unavailable, the tools return the cached copy marked `"stale": true` instead of failing

Every builder run also writes its build as a markdown file under `workspace/builds/`, so each run leaves a human-readable record on disk:

```bash
curl -X POST http://127.0.0.1:5000/tools/file_write -H 'Content-Type: application/json' -d '{"path": "notes/idea.md", "content": "Reality before assumption."}'
curl -X POST http://127.0.0.1:5000/tools/calendar_add -H 'Content-Type: application/json' -d '{"title": "Charter review", "when": "2026-08-01T10:00:00Z"}'
```

## Validated Hesitation (Friction Protocol)

OceanicOS attests instead of asserting (see [DECISIONS/0001-validated-hesitation.md](DECISIONS/0001-validated-hesitation.md)):

- Every builder run produces an attestation ([attestation.py](attestation.py)): a SHA-256 hash of the build record, a deterministic confidence score, the 0.74 threshold it was judged against, and the source trail of pipeline stages.
- Builds below the threshold are **held** — their review is never auto-approved, and the evolution report calls for a human to resolve them. Running a build without a context is treated as missing evidence.
- `POST /models/consensus` runs every matching adapter in parallel and surfaces disagreement (`"dissent": true`) as the primary output.
- The browser UI is a monochrome verification terminal with a deliberate 2.5-second render delay; it reports hashes, confidence, and source trails, never a single "final" answer.
- `GET /builds/export` degrades the build ledger gracefully into a spreadsheet (CSV); `GET /builds/export.txt` degrades one step further, into plain text.
- `GET /cvi` reports the Composite Verification Index — mean attestation confidence discounted by the held ratio; no evidence scores 0.0.
- `GET /cvi/history` returns the CVI as a time series — the trend behind the headline number, recorded change-only at the points it can move (a build, a held-review decision), scoped by `?actor=` and capped by `?limit=`. The console draws a sparkline from it (see [DECISIONS/0023](DECISIONS/0023-cvi-trend-history.md)).
- `GET /metrics` exposes platform state (CVI, held queue, SLA breaches, chain integrity, builds, adapters) in the **Prometheus text exposition format** — scrapeable by any monitoring stack with no custom integration. Aggregate scalars only, public like `/cvi` (see [DECISIONS/0020](DECISIONS/0020-prometheus-metrics.md)).
- `GET /attestations` filters the record server-side with fully parameterized query params — `status` (attested/held), `min_confidence`/`max_confidence`, `subject` (substring), `since` (ISO), `limit`, plus `actor`. No params returns the whole record. Every filter is a bound parameter, so a SQL payload is matched as a literal, never executed (see [DECISIONS/0021](DECISIONS/0021-attestation-search.md)).
- `GET /attestations/verify` walks the attestation hash chain and reports whether the ledger is intact — the record attests to itself. Each attestation carries the previous entry's hash and its own, so any retroactive edit breaks the chain and the walk returns the id of the first broken link (see [DECISIONS/0011](DECISIONS/0011-tamper-evident-ledger.md)). It also validates the latest signed checkpoint: `trustworthy` is true only when the chain is intact, the sealed head is still reproduced, and its signature validates under the current key.
- `POST /attestations/checkpoint` (admin) seals the current chain head with an HMAC signature keyed by `OCEANICOS_SIGNING_KEY` — a secret that never touches the database. This raises the bar from tamper-*evident* to tamper-*resistant*: an attacker who rewrites the ledger and recomputes the chain forward still can't forge a checkpoint matching their new head without the key, so `verify` reports `trustworthy: false` (see [DECISIONS/0012](DECISIONS/0012-signed-checkpoints.md)). Returns 503 if no key is configured, 409 if the chain is already broken. Set `OCEANICOS_CHECKPOINT_EVERY=N` to seal the head automatically every N attestations so the signed guarantee operates without a human in the loop (default 0 = manual-only; `/admin/overview` reports the active `checkpoint_policy`; see [DECISIONS/0014](DECISIONS/0014-automatic-checkpoint-cadence.md)).
- `POST /attestations/verify-bundle` verifies a bundle the caller holds — the online twin of `verify_ledger.py`, running the same pure `verify_bundle` so the two can't diverge. Chain integrity always; the signature validates only for bundles this server sealed (no key is accepted over the wire). See [DECISIONS/0029](DECISIONS/0029-online-bundle-verification.md).
- `GET /attestations/export` returns the whole sealed record — every attestation and checkpoint — as a self-contained JSON bundle. The standalone `verify_ledger.py` re-walks that bundle **offline**, with no service, database, or engine (`python verify_ledger.py --key <key> bundle.json`; exit 0 when intact and, with the key, trustworthy). Trust in the record becomes portable, not service-bound — the attestation ledger's answer to "the ground truth survives without the system" (see [DECISIONS/0013](DECISIONS/0013-portable-verifiable-export.md)).
- `POST /models/consensus` convenes a 4-member dissent panel — three model heuristics plus a deterministic **rules engine** anchor ("3 competing LLMs + 1 rules engine"). `POST /rules/evaluate` returns the rules engine's verdict *with the named rules that fired and the reason each exists* — the one panel member that explains itself (see [DECISIONS/0017](DECISIONS/0017-rules-engine-panel-anchor.md)).
- Held attestations get a stewardship resolution path (the Arbiter tier's held-review SLA, made real): `GET /attestations/held` (admin) lists them with a `pending`/`released`/`upheld` status; `POST /attestations/<id>/review` records a steward's `release` or `uphold` with a required reason; `GET /attestations/<id>/reviews` is the trail. Reviews are append-only records in their own table — the held attestation is never edited, so the chain stays intact — and a documented release lifts the item out of the CVI's held ratio (see [DECISIONS/0018](DECISIONS/0018-held-review-workflow.md)).
- The SLA is timed, not just named: each held item carries an `sla` block — `pending` items report `age_seconds` and `sla_breached`; `decided` items report `decision_seconds` and `within_sla` (time to a decision, release or uphold). `OCEANICOS_HELD_SLA_SECONDS` sets the window (default 24h; `0` disables), and `/admin/overview` reports `held_sla_breached` (see [DECISIONS/0019](DECISIONS/0019-held-review-sla-aging.md)).
- `GET /observer` reports the root process: stateless, sole read/write head, sigil checksum `0xΩ∞v`, a real SHA-256 of the constitution, and the ratified manifest's hash plus whether the Anchor is present.
- `GET /anchor` surfaces the **Anchor of Last Resort** (`boot/anchor_2019.txt`) — a fixed 2019 dataset (the Gregorian calendar of 2019) that answers offline with no service, database, or model in the loop; `?date=2019-07-04` looks a row up straight from the cache. It's the floor of graceful degradation: past the CSV, past the spreadsheet, one stale `.txt` that cannot fail (see [DECISIONS/0015](DECISIONS/0015-boot-manifest-and-anchor.md)).
- The stack boots from a ratified, hash-attested manifest: `python oceanic_os.py --boot boot/init.v1 --state stateless --exit 0` (or `make boot`) instantiates the live components each manifest layer maps to and reports their real status — the threshold in force, the dissent panel's size, the checkpoint policy, the manifest hash, `anchor: present`. It always exits 0; the system continues.
- The system states one name of itself, root to charter (`/` → Ω∞v Compiler → OceanicOS → Living Agnostic Charter). The boot banner and `/observer` both speak it from the single source in [`identity.py`](identity.py); see [TREE.md](TREE.md) and [DECISIONS/0016](DECISIONS/0016-canonical-identity.md).
- The platform is offered commercially as Verification-as-a-Service — see [docs/VAAS.md](docs/VAAS.md) and `GET /pricing`.

## Identity and Multi-User Attribution

Register for a token and every action you take is attributed to you (see [DECISIONS/0002](DECISIONS/0002-identity-and-attribution.md)):

```bash
curl -X POST http://127.0.0.1:5000/auth/register -H 'Content-Type: application/json' -d '{"username": "alice"}'
# -> {"username": "alice", "token": "<shown once>", "created_at": "..."}
curl -X POST http://127.0.0.1:5000/builder/run -H 'Content-Type: application/json' -H 'Authorization: Bearer <token>' -d '{"task": "Ship it"}'
# the build ledger and attestation trail now carry actor: alice
```

Attribution is always on (unauthenticated requests are recorded as `anonymous`). To require a valid token on protected endpoints, set `OCEANICOS_REQUIRE_AUTH=1` — unauthenticated calls then return 401, while `/health`, `/observer`, and `/pricing` stay public. Tokens are stored only as SHA-256 hashes and shown exactly once.

Your data is addressable as yours (see [DECISIONS/0003](DECISIONS/0003-per-user-data-scoping.md)): the `/me/*` views return only the authenticated actor's builds, attestations, memory, and CVI, while the global reads accept an optional `?actor=` filter and otherwise return the whole record — scoping is a lens, transparency is the default.

```bash
curl http://127.0.0.1:5000/me/builds -H 'Authorization: Bearer <token>'   # only your builds
curl http://127.0.0.1:5000/me/cvi -H 'Authorization: Bearer <token>'      # your verification index
```

Stewardship is a role, not a free-for-all (see [DECISIONS/0004](DECISIONS/0004-admin-stewardship-role.md)): admins are appointed out-of-band with `OCEANICOS_ADMIN_USERS` (comma-separated usernames) and get aggregate cross-actor views (`/admin/overview`, `/admin/users`) — platform health and per-actor build counts, not the content of members' private slices. Non-admins get 403. Members can't promote themselves.

The VaaS pricing tiers are enforced as rolling-window build quotas (see [DECISIONS/0005](DECISIONS/0005-per-tier-quotas.md) and [DECISIONS/0009](DECISIONS/0009-windowed-rate-limits.md)): new accounts default to **attestor** (10 builds/hour), and an admin assigns tiers with `POST /admin/users/<username>/tier`. `/builder/run` returns **429** once a named actor exceeds its rate in the current window (the response carries `resets_at`); usage recovers continuously as builds age out. `GET /me/quota` shows `used`, `window_seconds`, and `resets_at`. The window is configurable via `OCEANICOS_QUOTA_WINDOW` (default 3600s); the anonymous open path is unmetered. Metered responses also carry the standard `X-RateLimit-Limit`/`-Remaining`/`-Reset` headers, and a 429 adds `Retry-After` — so clients pace and back off by convention, no body parsing (see [DECISIONS/0024](DECISIONS/0024-rate-limit-headers.md)); unlimited (sovereign) tiers emit none.

The whole journey, prompt 1 to now, is compressed in [docs/COMPRESS.md](docs/COMPRESS.md) — `Gap → VaaS → Ω∞v → Observer → 0`.

```bash
OCEANICOS_ADMIN_USERS=root python app.py
# register "root" -> role: admin; /admin/overview then returns 200 for root's token, 403 for everyone else
```

## Brand

The identity carries the charter — fluid, agnostic, verified (see [docs/BRAND.md](docs/BRAND.md)). The verification terminal opens on the canonical badge as a brief boot splash, then hands off to the monochrome interface; the same badge is the favicon.

## Scope

This charter is intended to guide:

- project governance and collaboration
- architectural and technical direction
- ethical and social considerations
- long-term stewardship of the initiative

It is not meant to be a rigid rulebook. Instead, it should evolve as the project learns and grows.

## First Commitments

- Keep the charter simple and legible.
- Prefer reversible and transparent choices.
- Document decisions in a way that future contributors can understand.
- Treat the charter as a living document, not a final verdict.

## How to Contribute

Contributions can be made by proposing edits, refining principles, or suggesting new sections that improve clarity and usefulness. The best contributions are grounded in the project’s values and written in a way that helps others participate.

## Becoming

OceanicOS is a process, not a fixed destination. To continue becoming means:

- practicing iteration over perfection
- keeping the charter visible and easy to update
- testing ideas with small, real experiments
- learning from what works and what doesn’t
- making space for new contributors to shape the project

This repository is the first seed of that process. The next stage is to turn this charter into accessible practices and shared outcomes.

## Vision

OceanicOS is meant to be a living, agnostic approach to building systems that are adaptable, collaborative, and human-centered. The charter should help maintain momentum while avoiding rigid, gatekeeping structures.

## Next Steps

- Clarify the project’s target audience and use cases.
- Define the first practical goals or deliverables for OceanicOS.
- Add a short roadmap or milestones section.
- Establish a lightweight process for decision-making and updates.
- Invite collaborators to review and refine the charter.
- Implement the first working orchestration loop around planning, memory, and tool use.

## Related resources

- See [ROADMAP.md](ROADMAP.md) for the initial milestones and goals.
- See [CONSTITUTION.md](CONSTITUTION.md) for the rules that guide the project.
