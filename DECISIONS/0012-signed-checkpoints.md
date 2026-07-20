# 0012 — Signed Checkpoints Over the Chain Head

## Context

Round 11 (DECISIONS/0011) made the attestation ledger tamper-*evident*: a hash
chain, so any in-place edit breaks a link. That record itself named the limit —
an attacker with write access could rewrite a past entry and recompute every
later hash, producing a chain that is internally consistent and passes the
walk. Tamper-evident is not tamper-resistant. The honest next step, asked for
directly, was to close that gap the right way rather than leave the caveat
standing.

## Decision

Seal the chain head with a signature only the operator's key can produce.

- A **checkpoint** is an HMAC-SHA256 over `f"{head_hash}:{length}"`, keyed by
  `OCEANICOS_SIGNING_KEY` — a secret held in the process environment, never
  written to the database. Checkpoints live in their own table (`head_hash`,
  `length`, `created_at`, `signature`).
- `AttestationEngine.checkpoint()` seals the current head. It refuses to sign a
  chain that is already broken — a checkpoint should only ever bless the truth —
  and raises if no key is configured.
- `AttestationEngine.verify()` composes both defenses: the chain walk (in-place
  edits) *and* the latest checkpoint (whole rewrites). It reports `trustworthy`
  true only when the chain is intact, the sealed head is still reproduced at the
  sealed length, and the signature validates under the current key.
- `POST /attestations/checkpoint` (admin, 503 without a key, 409 on a broken
  chain) seals; `GET /attestations/verify` returns the composed report;
  `/admin/overview` carries it.

## Consequences

- The bar moves from tamper-*evident* to tamper-*resistant*. An attacker who
  rewrites the ledger and honestly recomputes the chain forward passes the walk
  (`intact: true`) but fails the checkpoint: the new head no longer matches the
  signed one (`head_reproduced: false`), and they cannot forge a signature over
  their forged head without the key (`signature_valid` would be false if they
  tried to replace the checkpoint row). Either way `trustworthy` is false.
  Verified live: seal three attestations, rewrite the first and rebuild the
  chain forward — `/attestations/verify` reports `intact: true` yet
  `trustworthy: false`.
- The security rests on the key living outside the database. This defends the
  realistic threat — tampering with the DB at rest (a backup, a replica, a
  stolen file) — not an attacker who has also captured the running process's
  environment. That is the same trust boundary every signing scheme has, stated
  plainly rather than papered over.
- Optional by design: with no `OCEANICOS_SIGNING_KEY`, checkpoints are simply
  unavailable and `verify` falls back to the chain walk with
  `checkpointed: false`. No key, no false assurance.
- HMAC (symmetric, stdlib) over an asymmetric scheme: it adds no dependency and
  the verifier here is the operator, who already holds the key. If third-party
  verification without sharing the secret ever matters, an Ed25519 public-key
  checkpoint is the drop-in successor — the table and the verify composition
  don't change.
