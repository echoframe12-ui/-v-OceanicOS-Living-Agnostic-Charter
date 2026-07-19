# Layer 6: Applications

The surfaces people actually touch.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| HTTP API | `app.py` | ~30 endpoints covering plans, memory, tools, workflows, models, builds, attestations, reviews, decisions, artifacts, dashboard, and the builder |
| Verification terminal | `templates/index.html` | Monochrome, zero rounded corners, blinking cursor, deliberate 2.5s render delay; displays hashes, confidence, and source trails — never a single "final" answer |
| Demo entry points | `main.py`, `universal_builder.py` CLI | Runnable without the web layer |

## Principles applied

- Openness: every capability is reachable as a plain HTTP endpoint with JSON in and out.
- Explain significant reasoning: the terminal shows the attestation and source trail for every run.
