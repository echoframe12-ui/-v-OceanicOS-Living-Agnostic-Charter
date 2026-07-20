# 0018 — Held-Review Workflow

## Context

Attestations below the 0.74 threshold are marked `held` and counted against the
CVI's held ratio — and then nothing happened to them. There was no path for a
steward to look at a held item and decide, so the held pile only grew, and the
Arbiter tier's advertised "held-review SLA" (`docs/VAAS.md`, `/pricing`) had no
implementation behind it. A verification platform needs a resolution path for the
things it declined to pass.

## Decision

Add a stewardship review workflow for held attestations that never mutates the
ledger.

- **Reviews are append-only and separate.** `held_reviews.py` (`HeldReviewLog`,
  mirroring `usage.py`) stores each decision in its own table, referencing the
  held attestation by id and carrying the reviewer, verdict (`release` /
  `uphold`), reason, and timestamp. The held attestation — part of the hash
  chain — is never edited, so the tamper-evident record (round 17) stays intact.
- **Latest verdict wins.** `released_ids()` returns the attestations whose most
  recent review released them; a later `uphold` re-holds an item, a later
  `release` frees it. The record can change its mind without losing the history.
- **A documented release lifts the CVI.** `AttestationEngine.cvi` gained an
  optional `released_ids` parameter: released items no longer count against the
  held ratio. The engine takes the set as a parameter and never learns about
  reviews directly; the default keeps the round-16 behavior exactly.
- **Stewardship-gated.** The endpoints (`GET /attestations/held`, `POST
  /attestations/<id>/review`, `GET /attestations/<id>/reviews`) reuse
  `require_admin` (DECISIONS/0004). The tier *names* the SLA; the accountable
  steward *performs* it. Reviews are recorded in the usage audit too.

## Consequences

- The advertised SLA is now real, and honest to the ledger's principles: the
  held pile has a resolution path, and releasing an item is a documented,
  audited act — not a silent edit. Verified live: a held item shows `pending`,
  a release flips it to `released` and lifts the CVI (0.35 → 0.70 in the smoke),
  and `/attestations/verify` still reports `intact` afterward.
- Review credit is a lens, not a rewrite. The chain and the raw held status are
  untouched; the CVI simply reads the current release set when asked. Anyone
  auditing the bundle (round 19) sees the unchanged held attestation and can
  fetch the review trail beside it — the "why" is on the record.
- Validation is strict: a review targets an existing (`404`), still-held
  (`409`) attestation, with a known verdict and a non-empty reason (`400`). You
  cannot review what isn't held, and you cannot release without saying why.
- The reviewer is the steward (admin role), consistent with every other
  cross-actor stewardship view. If tiered self-service review is ever wanted,
  the gate is the single seam to change.
