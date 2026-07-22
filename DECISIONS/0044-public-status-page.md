# 0044 — Public Trust Status Page

## Context

The platform's verification posture was fully available but scattered across
machine surfaces — `/cvi`, `/metrics`, `/attestations/verify`, the drift-audit
trail — and the one human-facing surface, the console at `/`, is an *operator*
terminal: interactive, action-heavy (attest, review, seal, audit), and built for
someone driving the system. There was no page to simply *link someone to* that
answers "is the verification layer healthy right now?" at a glance, without an
account, without running anything, without reading JSON. A verification product
needs a status board as much as a bank needs a lobby clock.

## Decision

Add `GET /status` — a public, server-rendered trust posture page.

- **Server-rendered, no JavaScript.** The route assembles the live posture
  (`verify()`, `cvi()`, the held queue and its SLA, the latest checkpoint and
  drift audit, ledger totals) and renders `templates/status.html` with Jinja, so
  the page is complete on first byte and degrades to nothing. A 30-second
  `<meta refresh>` keeps it live; it embeds the round-49 CVI badge
  (`/badge/cvi.svg`) rather than recomputing anything.
- **A single posture verdict.** `TRUSTWORTHY` (chain intact, head reproduced and
  signature valid), `INTACT` (chain intact but not yet sealed to trustworthy), or
  `BROKEN` (with the broken-at id) — the honest three-state summary above the
  detail tiles.
- **Read-only and public**, like `/cvi` and `/metrics`: aggregate scalars only,
  no per-actor content, no actions. Distinct from the console by design.

## Consequences

- The posture is now legible to a human in one glance, and the page is honest
  about the difference between integrity and confidence: verified live, a sealed
  four-entry record shows `TRUSTWORTHY` in green while the CVI badge reads `0.58`
  in orange, because a held `0.5` entry drags confidence below the `0.74`
  threshold. The chain is trustworthy *and* the index is middling — two true
  things the board shows side by side rather than collapsing into one.
- All four postures were exercised end to end: an empty and an unsealed record
  read `INTACT`, a checkpoint promotes it to `TRUSTWORTHY`, and tampering a row
  in the database drops it to `BROKEN at #1`.
- Presentation only, a thin server-side read over methods that already exist — no
  new state, no new persistence, the same discipline the console holds
  (`DECISIONS/0034`): the page reads the record, it never becomes a second copy
  of it.
- A Jinja lesson worth recording: literal `&amp;` inside a `{{ }}` expression is
  double-escaped by autoescape and renders as visible `&amp;`; a bare `&` in the
  expression string is escaped once and renders as `&`. Literal template text
  outside `{{ }}` is untouched. Caught in the live screenshot, not the unit test.
