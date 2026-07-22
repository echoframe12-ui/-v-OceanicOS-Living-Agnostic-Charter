# 0029 — Online Bundle Verification

## Context

Round 13 (DECISIONS/0013) made the sealed ledger portable: `/attestations/export`
emits a self-contained bundle, and `verify_ledger.py` re-walks it **offline** with
no service. That covers the "trust survives the system" case. But the common case
is the opposite: a client *holding* a bundle wants a quick answer — "is this
intact?" — without installing the verifier or importing the hashing primitives.
There was no online way to check a supplied bundle.

## Decision

Add `POST /attestations/verify-bundle`, the online twin of the offline verifier.

- It runs the **same pure `verify_bundle`** the CLI uses (`verify_ledger.py`), so
  the online and offline answers cannot diverge — one function, two callers.
- Chain integrity (`intact`, `broken_at`) is always checked. The signed
  checkpoint validates only when this server holds the key the bundle was sealed
  with; the key is read from the server's own environment and **never accepted
  over the wire** — a caller cannot submit a key, so the endpoint can't be turned
  into a signing oracle.
- The body must be an exported bundle (a dict with an `attestations` list);
  anything else is a `400`.

## Consequences

- A client can verify a bundle it holds with one request: verified live — a good
  bundle returns `intact: true`, a bundle with one edited field returns
  `intact: false, broken_at: 1`, and a malformed body returns `400`.
- Reuse is the safeguard: because the endpoint and `verify_ledger.py` share the
  exact `verify_bundle`, a change to the verification logic updates both at once.
  The online endpoint is convenience; the offline verifier remains the
  trust-anchor for the "no service" case, and they agree by construction.
- Signature validation is deliberately server-key-only. Validating an arbitrary
  bundle's signature would require the caller's key, and accepting secrets over
  HTTP is exactly what the signing design (DECISIONS/0012) refuses. So the
  endpoint proves chain integrity universally and signed-trust only for bundles
  this instance sealed — an honest scope, not a false one.
- Read-only and stateless: it verifies the submitted bytes and touches no ledger
  state, so it is safe to leave public like the other read surfaces.
