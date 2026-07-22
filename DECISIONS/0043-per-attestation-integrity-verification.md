# 0043 — Per-Attestation Integrity Verification

## Context

The ledger could prove two things: that the *whole* chain was intact
(`/attestations/verify`, `verify_chain`) and that an entry existed at a position
(`/attestations/<id>/receipt`). But it could not answer the narrowest, most
common auditor's question directly — *is **this one** attestation untampered and
correctly linked?* The receipt reported `chain_intact` (a property of the entire
record), not the integrity of the specific entry it was a receipt for. A client
holding a receipt for entry #42 still had to trust the aggregate verdict to
believe #42 itself.

## Decision

Add a per-entry integrity check and let the receipt certify its own entry.

- `AttestationEngine.verify_entry(att_id)` recomputes the entry's `link_hash`
  from its recorded fields and its predecessor's hash, and reports two
  independent facts: `entry_hash_matches` (the stored hash equals the recomputed
  one — the entry's own fields are untampered) and `prev_hash_matches` (its
  stored `prev_hash` equals the actual predecessor's hash, GENESIS for the first
  row — it is linked at the right place). `intact` is their conjunction. Returns
  None for a missing id.
- `GET /attestations/<id>/verify` exposes it — public, like the receipt it backs,
  and a focused companion to the whole-chain `/attestations/verify`.
- `receipt()` now carries `entry_intact`, computed the same way, so a receipt is
  self-certifying: it proves the specific entry, not merely that the chain around
  it is whole.

## Consequences

- The two matches are reported separately on purpose. A tamper to an entry's own
  fields flips `entry_hash_matches` while leaving `prev_hash_matches` true, which
  localises the damage to the entry's content rather than its position — verified
  live: flipping a held row's status straight in the database turns
  `entry_hash_matches` and `intact` false while `prev_hash_matches` stays true,
  and the recomputed hash visibly differs from the stored one. The receipt's
  `entry_intact` follows.
- This is the per-item proof the positioning note names ("was *this exact output*
  verified, and is its record intact") made literal at the level of a single
  attestation, not just the content-hash lookup.
- No new state and no schema change: `verify_entry` and the receipt's
  `entry_intact` are derived at read time from the same fields `verify_chain`
  already covers, so they can never disagree with the whole-chain verdict for an
  intact record, and there was nothing to migrate.
- The check is honest about scope: content itself is not stored (only its
  `sha256`), so `verify_entry` proves the *record* of the attestation is
  untampered and correctly linked — the content-hash match against a held artifact
  remains the job of `/attestations/lookup` (`DECISIONS/0035`). The two together
  answer "is this the same output" and "is its attestation intact".
