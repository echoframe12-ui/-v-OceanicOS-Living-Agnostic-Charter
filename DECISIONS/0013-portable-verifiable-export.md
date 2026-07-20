# 0013 — Portable, Independently-Verifiable Ledger Export

## Context

Rounds 10–12 (DECISIONS/0010–0012) made the attestation ledger persistent,
tamper-evident, and tamper-resistant. But every one of those guarantees could
only be *checked* by calling the running service: `/attestations/verify` reads
the live database through the live engine. Trust in the record was
service-bound. If the service is down, compromised, or simply not the party you
trust, there was no way to confirm the record for yourself.

The repository already treats this as a principle worth honoring. Layer 8:
*"one SQLite file and one CSV export stand between the platform and total loss"*
and *"the ground truth survives without the system."* The builds ledger backs it
with `/builds/export`. The attestation ledger — the record the CVI and every
trust claim rest on — did not.

## Decision

Export the sealed record as a self-contained bundle, and verify it offline.

- `AttestationEngine.export()` returns `{version, exported_at, genesis,
  attestations, checkpoints}` — the whole chain and every seal in one JSON
  document. `GET /attestations/export` serves it as an attachment.
- `verify_ledger.py` is a standalone stdlib-only script. It imports only the
  pure functions the engine uses — `link_hash`, `GENESIS_HASH`,
  `checkpoint_signature` — and recomputes the full integrity report from a
  bundle alone: no Flask, no sqlite, no engine, no running service. With `--key`
  it also validates the signed checkpoint. It exits 0 when the record is intact
  (and, given a key, trustworthy) and non-zero otherwise, so it doubles as a CI
  or cron integrity gate.
- The HMAC was extracted into the module-level `checkpoint_signature` so the
  engine and the offline verifier sign and check identically — one source of
  truth, exactly as `link_hash` already is for the chain. The verifier cannot
  drift from the engine because it *is* the engine's own primitives.

## Consequences

- Trust in the record is now portable. Anyone holding the bundle can confirm the
  chain was not edited in place; anyone also holding the key can confirm it was
  not rewritten wholesale. Neither needs the service running. Verified live: a
  bundle exported from a running server verifies as `trustworthy` **after the
  server is stopped**, and a single edited field in the bundle drops the
  verifier to a non-zero exit reporting the broken id.
- The export carries actor names, consistent with `/attestations` already
  exposing the global record; scoping remains a lens, transparency the default.
- The bundle is the attestation ledger's CSV: the honest, low-tech artifact that
  outlives the platform. If the whole system is lost, the last export still
  proves what was verified.
- This does not need or add a dependency, and it is fully exercised in the test
  suite and by a live smoke — unlike the Ed25519 public-key successor named in
  DECISIONS/0012, which the environment's broken crypto backend could not run.
  When public-key verification (third parties who should verify without holding
  the secret) becomes a real need, `checkpoint_signature` is the single seam to
  swap, and this bundle format and verifier compose over it unchanged.
