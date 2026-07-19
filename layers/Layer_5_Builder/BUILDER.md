# Layer 5: Builder

The universal builder (`universal_builder.py`) is the working implementation of
this layer. Each run executes a ten-stage pipeline:

1. `plan` — the planner produces structured steps with a trace
2. `workflow` — the plan becomes an executed workflow
3. `route` — the task is routed to the best-matching model adapter
4. `agent` — the agent loop records observable events
5. `review` — the run is submitted for review and approved
6. `decision` — the decision registry records why the run happened
7. `artifact` — an artifact entry is created and the dashboard updated
8. `workspace` — the build is written as a markdown file under `workspace/builds/`
9. `memory` — a memory entry is stored in SQLite
10. `ledger` — the run is persisted to the builds ledger, surviving restarts

## Tool plugins

The builder installs the tool plugins from `tool_plugins.py` on its service:

- `file_list` / `file_read` / `file_write` — sandboxed to the workspace
  directory (`OCEANICOS_WORKSPACE`, default `workspace/`); paths that escape
  the sandbox are rejected
- `calendar_add` / `calendar_list` — events persisted to the OceanicOS SQLite
  database

## Principles applied

- Preserve provenance and history: every run leaves a plan trace, a ledger
  row, a memory entry, and a human-readable build file.
- Humans remain accountable: each run passes through the review engine and
  decision registry before its artifact is recorded.
