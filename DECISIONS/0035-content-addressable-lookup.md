# 0035 — Content-Addressable Attestation Lookup

## Context

The ledger hashes every content on the way in (the `sha256` on each
attestation), but there was no way back: a party holding an output — a report, a
decision, a generated artifact — could not ask the record "was *this exact
content* attested, and with what confidence?" Verification ran forward (attest,
then check the chain) but not from an artifact in hand back to its attestation.
For a platform whose product is proof, that reverse lookup is the natural other
half.

## Decision

Add content-addressable lookup.

- `AttestationEngine.by_content_hash(sha256)` returns every attestation of a
  given content hash (the same content may be attested more than once).
- `POST /attestations/lookup` takes either `content` (hashed server-side with the
  same SHA-256 the engine uses) or a `sha256` directly, and returns
  `{sha256, found, matches}`. A body with neither is a `400`.

## Consequences

- The loop closes: a caller recomputes an artifact's hash — or lets the server do
  it from the raw content — and learns whether it was attested and with what
  confidence and status. Verified live — attested content returns
  `found: true` with its confidence, content that was never attested returns
  `found: false`, and a missing body returns `400`.
- Hashing `content` server-side uses the exact `hashlib.sha256(...).hexdigest()`
  the engine applies at attest time, so a lookup by content and the original
  attestation agree by construction — the same primitive on both ends.
- It returns *all* matches, not one: the same content attested twice (e.g. by two
  actors, or before and after a revision) is a real and meaningful case, and
  collapsing it would hide that the artifact has more than one record.
- Read-only and public, consistent with the other verification reads. It exposes
  only attestations that already exist; it cannot create one, and knowing a hash
  reveals nothing the record doesn't already publish.
