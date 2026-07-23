# 0055 — The Doctrine as a Code-Backed Map

## Context

The Ω∞v Doctrine is the system's compressed self-definition — premise, product,
interface, backend, infrastructure, security, OS, governance, final state. It had
always lived as prose (the identity trees, `TREE.md`, `docs/COMPRESS.md`). But a
doctrine that only asserts is exactly what this platform refuses in every other
context: an unverified claim. A reader had no way to tell which layers were
actually built from which were aspiration, and nothing stopped the doctrine from
drifting as the code moved beneath it. The one document describing the whole
system was the one document held to no standard of evidence.

## Decision

Make the Doctrine code-backed and self-verifying.

- `doctrine.py` holds the Doctrine as structured data: each layer names the
  endpoints, modules, decision records, and documents that implement it, plus an
  honest `shipped` flag. `GET /doctrine` serves it (with the axioms, the embedded
  constitution, and the checksum).
- `DOCTRINE.md` is the human view, with an *As Shipped* table mapping each layer
  to its code and marking the two physical layers as not shipped.
- `tests/test_doctrine.py` enforces the claim: for every layer marked `shipped`,
  each cited endpoint must resolve in the live URL map, each module must import,
  each `DECISIONS/NNNN` must exist, and each document must be on disk. A layer
  that is not shipped must say so and explain.

## Consequences

- The Doctrine is now held to the platform's own creed — *attest, don't assert*.
  Verified live and by test: 9 of 10 layers are `shipped`, every one of their
  citations resolves, and the tenth (`Security · Physical` — a compiled binary and
  a YubiKey) is honestly `shipped: false` with a note pointing at its software
  analogue (the operator-key HMAC and drift audits). The document cannot claim
  what the code does not provide.
- It cannot silently drift: if an endpoint is renamed, a module deleted, or a
  cited decision record removed, `test_doctrine.py` fails. The self-description is
  wired to the thing it describes, the same way `docs/POSITIONING.md`'s discipline
  ("every claim points at code") is now mechanically enforced rather than trusted.
- The honesty is structural, not editorial: the summary asserts
  `layers_shipped < layers_total`, so a future edit that quietly marks the
  physical layer as shipped — claiming a hardware key a repository cannot hold —
  breaks the suite. The Doctrine is required to admit what it has not built.
- This is the capstone of the "provable, not asserted" arc that runs through the
  receipt (one entry), the checkpoint (the ledger head), and the signed digest
  (the posture): now the *self-definition itself* is verifiable against the
  system it defines.
