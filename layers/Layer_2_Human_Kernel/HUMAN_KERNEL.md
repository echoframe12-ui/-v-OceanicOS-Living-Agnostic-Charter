# Layer 2: Human Kernel

The layer that keeps people in the loop — nothing ships on machine say-so alone.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| Review gate | `review.py` | Every builder run submits a review; approval is earned, not assumed |
| Validated hesitation | `attestation.py` + `universal_builder.py` | Builds below the 0.74 confidence threshold are held; their reviews stay pending until a human resolves them |
| Decision provenance | `decisions.py` + `DECISIONS/` | Why something happened is recorded alongside what happened |
| Human escalation | `universal_builder.py` `evolve()` | The evolution report surfaces held attestations and pending reviews as the first order of business |
| Identity & attribution | `auth.py` + `/auth/*` | Token-based identity; every build is attributed to an actor in the ledger and attestation trail. Tokens are hashed, never echoed; enforcement is env-gated (`OCEANICOS_REQUIRE_AUTH`) — see [DECISIONS/0002](../../DECISIONS/0002-identity-and-attribution.md) |

## Principles applied

- Humans remain accountable: the pipeline refuses to automate the handshake.
- Respect dignity, privacy, and consent: the system asks for a human squint instead of assuming one.
