# 0031 — Serve the Decision Log

## Context

The platform records every significant design choice as a numbered Architecture
Decision Record in `DECISIONS/` — thirty of them by now, each with its context,
decision, and consequences. But that governance lived only in the repo. A system
whose whole premise is accountability and provenance should be able to show, at
runtime, *why* it is the way it is — not require someone to go read the source
tree. The reasoning was documented but not part of the running system.

## Decision

Serve the ADRs from the API.

- `adr.py` reads `DECISIONS/[0-9]*.md`: `list_adr()` returns
  `{number, title, filename}` per record (title parsed from the first heading,
  stripping the `Decision NNNN:` / `NNNN —` prefix), ordered by number;
  `get_adr(n)` returns one with its full markdown, or `None`.
- `GET /adr` lists them; `GET /adr/<n>` returns one (404 for a missing number).
  Public — the decision log is transparency, like the constitution SHA on
  `/observer`. The console links to it.

## Consequences

- The system now surfaces its own governance: verified live — `/adr` lists all
  30 records with clean titles ("Adopt the Validated Hesitation Protocol",
  "Signed Checkpoints Over the Chain Head", …), `/adr/12` returns the full text,
  and `/adr/9999` is a 404. The "why" travels with the running service, not just
  the repo.
- It reads the files at request time, so it can never drift from the actual
  records — the same reason the OpenAPI spec (0025) is generated, applied to
  governance: the source of truth is the source, served directly.
- Distinct from `/decisions` (the `DecisionRegistry` of build-time decisions the
  pipeline records): `/adr` is the *architecture* decision log, the human design
  history. Two different kinds of decision, two endpoints, no overlap.
- Read-only and dependency-free — a filesystem read and a heading parse. The
  parser tolerates both heading styles present in the corpus
  (`# Decision NNNN: …` and `# NNNN — …`), so older and newer records serve
  uniformly.
