# 0011 — Tamper-Evident Attestation Ledger

## Context

Round 10 gave the attestation record one home in SQLite, shared across workers.
But a shared record is not a trustworthy one: anyone with access to the database
file could edit a past attestation — flip a `held` build to `attested`, raise a
confidence — and nothing would show. A platform whose entire premise is
"attest, don't assert" cannot keep a ledger that it can't itself verify. The
record needed to attest to itself.

## Decision

Make the attestation record a **hash chain**.

- Each attestation stores `prev_hash` (the previous entry's hash) and
  `entry_hash = sha256(prev_hash + canonical(content fields))`, covering
  subject, actor, content sha256, confidence, threshold, status, sources, and
  timestamp. The first entry links to a fixed `GENESIS_HASH`.
- Writes acquire the SQLite write lock (`BEGIN IMMEDIATE`) before reading the
  chain tail, so two concurrent workers cannot link two new entries onto the
  same predecessor and fork the chain.
- `AttestationEngine.verify_chain()` walks the ledger, recomputes each link, and
  returns `{intact, length, broken_at, head}`. `broken_at` is the id of the
  first entry whose stored hash no longer matches — the point at or before which
  the record was altered.
- `GET /attestations/verify` exposes the walk; `/admin/overview` includes the
  chain report alongside the CVI.

## Consequences

- The ledger is now tamper-evident: editing any past attestation changes its
  hash, which every later entry's `prev_hash` was built on, so the break
  propagates to the head and the walk finds it. Verified live — a direct
  `UPDATE` to a past row's confidence flips `/attestations/verify` to
  `intact: false` with the tampered id.
- Tamper-*evident*, not tamper-*proof*: a determined attacker with write access
  could recompute the whole chain forward from an edit. That is a much higher
  bar than a silent single-row edit, and the honest failure mode (a broken
  chain) is the point. A co-signed or externally-anchored head would raise the
  bar further; deferred until there is a reason to trust an external anchor more
  than the operator.
- No API change to `attest`; entries simply carry two more fields. A pre-chain
  database is migrated forward with `ALTER TABLE ADD COLUMN` on startup, so
  existing rows are preserved (they read as a broken chain from the first, which
  is the honest report for links that were never signed).
- The CVI now sits on a record that can be checked, not just read.
