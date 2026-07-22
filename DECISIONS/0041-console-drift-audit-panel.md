# 0041 — Console Drift-Audit Panel

## Context

Round 39 (DECISIONS/0039) added perpetual drift audits — a persistent trail of
integrity checks and a `POST /attestations/audit` to run one — but the console
(the platform's face) had no way to see or trigger them. The integrity story was
complete in the API and absent in the UI, the same drift the round-40 catch-up
addressed for stats and receipts.

## Decision

Surface the audit trail in the Integrity panel.

- A **Run Drift Audit** button posts `/attestations/audit` with the session token
  (admin), reporting `intact` / `BROKEN @ id`.
- A **drift audit trail** below the panel loads `/attestations/audits?limit=6`
  (public), showing each check newest-first: timestamp, chain length, and
  intact/trustworthy or broken-at.
- Re-verify and Seal-Checkpoint now refresh the trail too, so an audit recorded
  at a checkpoint appears immediately.

## Consequences

- The integrity story is now visible end to end in the console: the chain state,
  the seal, *and* the history of checks. Verified live — the panel renders the
  button and trail, and every other panel still loads (no JS regression).
- Presentation only, a thin client over existing endpoints (`/attestations/audit`
  and `/attestations/audits`), so there is no new state or logic — the same
  discipline as the rest of the console (DECISIONS/0034): the UI reads from the
  API rather than restating it.
- Admin actions fail closed in the UI as they do on the server: without a steward
  token the audit button reports that one is required, mirroring the 403.
