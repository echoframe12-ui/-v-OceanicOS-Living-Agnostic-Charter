# 0003 — Per-User Data Scoping

## Context

Decision 0002 gave the platform identity: every build is attributed to an
actor. Attribution alone is visibility, not separation — any user could still
read every other user's builds, memory, and attestations. A multi-user
platform that respects dignity and consent needs each actor to be able to see
their own work as a coherent slice.

## Decision

Scope the three actor-bearing stores by actor:

- **Builds** — `list_builds(actor=...)` filters the ledger.
- **Memory** — the `memory` table gains an `actor` column; `store_memory`
  records it and `search_memory(query, actor=...)` filters.
- **Attestations** — `attest(..., actor=...)` records the actor; `list(actor=...)`
  and `cvi(actor=...)` scope to it.

Two access patterns:

1. **Scoped self-views** (`/me/builds`, `/me/attestations`, `/me/memory`,
   `/me/cvi`) require a token and return only the authenticated actor's data.
2. **Optional filters** on the global reads (`/builds?actor=`,
   `/attestations?actor=`, `/memory?actor=`) — unfiltered still returns the
   whole record, so the platform stays transparent and auditable by default.

## Consequences

- Each actor gets a private slice without the platform becoming opaque:
  transparency is the default, scoping is a lens.
- Backward compatible — every scoping parameter defaults to "all", so existing
  callers and the reference deployment are unchanged.
- Charter alignment: respect for consent (your data is addressable as yours)
  held in tension with openness (the whole record remains inspectable) — the
  two coexist rather than trading off.
