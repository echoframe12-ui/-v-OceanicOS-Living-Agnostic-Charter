# Layer 6: Applications

The surfaces people actually touch.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| HTTP API | `app.py` | ~60 endpoints covering plans, memory, tools, workflows, models, builds, attestations, held-review, checkpoints, CVI + history, quotas, metrics, rules, anchor, decisions, artifacts, dashboard, and the builder |
| Self-describing API | `openapi.py` + `/openapi.json` | A valid OpenAPI 3 doc generated from the live route table — accurate by construction, never drifts; see [DECISIONS/0025](../../DECISIONS/0025-self-describing-api.md) |
| Interactive console | `templates/index.html` | Single-page console exercising every subsystem live — tiles, identity, build+attest (deliberate 2.5s render delay), the dissent panel, rules, ledger search, integrity + checkpoint, held-review SLA, anchor, metrics, pricing; see [DECISIONS/0022](../../DECISIONS/0022-interactive-console.md) |
| Demo entry points | `main.py`, `universal_builder.py` CLI | Runnable without the web layer |

## Principles applied

- Openness: every capability is reachable as a plain HTTP endpoint with JSON in and out.
- Explain significant reasoning: the terminal shows the attestation and source trail for every run.
