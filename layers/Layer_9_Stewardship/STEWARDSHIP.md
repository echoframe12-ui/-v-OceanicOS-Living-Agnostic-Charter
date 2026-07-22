# Layer 9: Stewardship

The layer that looks after the whole — direction, memory, and accountability over time.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| Governing documents | `CONSTITUTION.md`, `GOVERNANCE.md`, `ROADMAP.md` | The rules and direction the code answers to |
| Self-direction | `universal_builder.py` `evolve()` | The platform reports its own state and proposes its own next steps, each grounded in what is actually installed and pending |
| Provenance | Builds ledger + `DECISIONS/` + attestations | What was built, why, and its content hash — all persisted |
| Long-term memory | `server.py` memory + `MEMORY.md` | Work survives sessions and restarts |
| Accountable stewardship | `auth.py` roles + `/admin/*` | An appointed admin role (via `OCEANICOS_ADMIN_USERS`) sees across actors — aggregate health, not member content; see [DECISIONS/0004](../../DECISIONS/0004-admin-stewardship-role.md) |
| Usage audit trail | `usage.py` + `/me/usage`, `/admin/usage` | Every metered event (build, quota block, tier change) is logged per actor with the tier in force — auditable, billable history; see [DECISIONS/0006](../../DECISIONS/0006-usage-metering-audit.md) |
| Held-review workflow | `held_reviews.py` + `/attestations/held`, `/attestations/<id>/review` | A steward reviews held attestations and records `release`/`uphold` with a reason. Append-only — the held item is never edited, so the chain stays intact — and a documented release lifts it out of the CVI's held ratio; see [DECISIONS/0018](../../DECISIONS/0018-held-review-workflow.md) |
| CVI trend history | `cvi_history.py` + `/cvi/history`, `/me/cvi/history` | The trust index recorded over time (change-only, at each build and held-review), platform-wide and per actor, so verification quality is a watchable trend; see [DECISIONS/0023](../../DECISIONS/0023-cvi-trend-history.md), [0030](../../DECISIONS/0030-per-actor-cvi-history.md) |
| Served decision log | `adr.py` + `/adr` | The platform serves its own Architecture Decision Records at runtime — the reasoning behind the system is inspectable from the running service, not just the repo; see [DECISIONS/0031](../../DECISIONS/0031-serve-the-decision-log.md) |

## Principles applied

- Steward for future generations: every round leaves the next contributor a ledger, a decision record, and a suggested next step.
- Learn continuously: the evolution report retires suggestions as they are fulfilled and names new frontiers.
