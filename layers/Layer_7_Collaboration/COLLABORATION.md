# Layer 7: Collaboration

How people and integrations join the work.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| Plugin registry | `plugins.py` | Integrations declare their capabilities; the registry is queryable at `/plugins` |
| Tool plugins | `tool_plugins.py` | Workspace files, calendar, and GitHub tools install onto the shared service |
| Review flow | `review.py` | Proposals, reviewers, and explicit approval states |
| Contribution norms | `CONTRIBUTING.md`, `GOVERNANCE.md` | The human-process counterpart to the code |
| Change history | Pull requests + `DECISIONS/` | Every evolution round lands as a reviewed PR with a recorded rationale |

## Principles applied

- Inclusivity: plugins and contributions extend the system without modifying its core.
- Interoperability: the GitHub tools speak the standard REST API; the calendar speaks plain SQLite.
