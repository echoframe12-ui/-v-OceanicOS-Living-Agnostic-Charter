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

## Principles applied

- Steward for future generations: every round leaves the next contributor a ledger, a decision record, and a suggested next step.
- Learn continuously: the evolution report retires suggestions as they are fulfilled and names new frontiers.
