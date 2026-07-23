# 0053 — Signed Status Digest

## Context

The platform reports its posture live (`/status`, `/status.json`), but a live
read is unprovable after the fact: an auditor handed a JSON blob claiming "we were
TRUSTWORTHY at 3pm" has no way to tell it came from the platform rather than a
text editor. The ledger has tamper-evident answers for the *record* — the signed
checkpoint, the per-attestation receipt — but the platform's report of its *own
health* was an unsigned assertion. For a platform whose creed is *attest, don't
assert*, the one claim it made without evidence was the claim about itself.

## Decision

Serve a signed, portable digest of the posture: `GET /status/digest`.

- A new pure module `status_digest.py` defines a fixed set of signable fields
  (posture, CVI, source coverage, chain intact/trustworthy/length, held
  pending/breached, checkpoint head, timestamp), a deterministic `canonical`
  form (sorted, compact), and `sign`/`verify` — an operator-key HMAC-SHA256, the
  same discipline as `checkpoint_signature`.
- The endpoint builds the payload from `_status_snapshot` and signs it with
  `OCEANICOS_SIGNING_KEY`. When no key is configured, `signed` is `false` and
  `signature` is `null` — the platform never claims a signature it cannot make.
- Verification is offline and third-party: anyone holding the digest and the key
  runs `status_digest.verify`, which recomputes the HMAC over the canonical form
  in constant time.

## Consequences

- The platform's self-report is now provable, not merely published: verified live,
  a signed digest reports `posture TRUSTWORTHY`, verifies `True` under the correct
  key, and `False` under a wrong key or after tampering a single field
  (`posture → BROKEN`). An auditor can archive the digest and later prove what the
  platform said, and that it really said it.
- The signature covers a canonical projection, not the raw response: extra,
  presentation-only fields (`signed`) are excluded from `SIGNABLE_FIELDS`, so
  re-signing and verification are unambiguous and a caller can attach display
  metadata without breaking the seal. Field order never matters — `canonical`
  sorts.
- It reuses the existing operator secret and the same HMAC construction as the
  checkpoint, so there is one key and one signing discipline across the platform,
  and the key still never leaves the process or touches the database.
- This is the platform-level analogue of the per-attestation receipt
  (`DECISIONS/0033`): the receipt proves one entry, the checkpoint seals the
  ledger head, and the digest signs the whole posture — three scopes of the same
  "provable, not asserted" guarantee. The digest is a snapshot in time by design;
  the `generated_at` it signs is what scopes the claim.
