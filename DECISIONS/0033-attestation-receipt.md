# 0033 — Per-Attestation Verification Receipt

## Context

The platform's whole premise is proof over assertion, and it had every piece of
the proof — content hashes, a tamper-evident chain, signed checkpoints — but no
way to get the proof for *one* attestation in a single place. A client that
wanted to present "this specific output was verified" had to stitch together
`/attestations`, `/attestations/verify`, and the checkpoint state themselves.
The evidence existed; the receipt didn't.

## Decision

Add `AttestationEngine.receipt(att_id)` and `GET /attestations/<id>/receipt`.

- The receipt locates the attestation and reports: the full record (subject,
  `sha256`, confidence, status, sources, timestamps, chain links), its
  `chain_position` (height) and the `chain_length`, whether the chain is
  `chain_intact`, and whether it is `sealed` — its position falls within a signed
  checkpoint's length. The latest checkpoint's length and time are included.
- `GET /attestations/<id>/receipt` returns it, 404 for a missing id. Public,
  read-only — a receipt is meant to be shown.

## Consequences

- A single attestation's proof is one request: verified live — attestation #1
  reports `pos 1/1, intact: true, sealed: false` before any checkpoint, flips to
  `sealed: true (checkpoint length 1)` once the head is sealed, and a missing id
  returns 404.
- `sealed` is precise about what a signature covers. An attestation is sealed
  only when its height is within a checkpoint's length, so an attestation added
  *after* the last seal correctly reports `sealed: false` — the receipt never
  claims signed coverage the checkpoint doesn't actually provide (tested).
- It composes existing guarantees rather than adding new state: the position
  comes from the same chain scan `verify_chain` walks, and the seal from the same
  `latest_checkpoint` the verifier uses, so the receipt agrees with
  `/attestations/verify` by construction.
- Read-only and public: the receipt is evidence to present, and it exposes only
  what `/attestations` already does plus derived position/seal facts — no secret,
  no new surface to protect.
