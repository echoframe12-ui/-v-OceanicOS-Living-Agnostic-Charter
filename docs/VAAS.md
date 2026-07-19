# Verification-as-a-Service (VaaS)

The trust/latency arbitrage, productized. OceanicOS occupies the gap
between instant generation and validated output: every deliverable is
attested (hash, confidence, source trail), dissent between models is
surfaced rather than hidden, below-threshold work is held for a human,
and the ledger degrades gracefully to CSV and plain text.

The 4-second render delay is not a limitation. It is the product — the
computational cost of verification, made visible.

## Tiers (USD / month)

| Tier | Price | Includes |
| --- | --- | --- |
| **Attestor** | $8,500 | Attestation API, Composite Verification Index (CVI), CSV/.txt ledger exports |
| **Arbiter** | $25,500 | Everything in Attestor + 3-adapter dissent panels, held-review SLAs |
| **Sovereign** | $85,000 | Everything in Arbiter + on-prem binary distribution, hardware-key (YubiKey) handoff, no source escrow |

Live tier data: `GET /pricing`.

## Composite Verification Index

`GET /cvi` reports platform-level trust as evidence, not vibes:

```
cvi = mean(attestation confidence) × (1 − held ratio)
```

No attestations means CVI 0.0 — no evidence, no trust.

## Node mounts

`POST /nodes {"name": "<node>"}` mounts a high-flux node. Every node is
stripped to charter-agnostic form — terrain, currency, and affiliation
attributes are removed uniformly, for every node, by design. The charter
is agnostic; its nodes are too.

## The Observer

`GET /observer` reports the root process: `root: /`, the sole read/write
head, stateless, carrying the sigil checksum `0xΩ∞v` alongside a real
SHA-256 of the constitution. Exit code 0. It continues.

## Openness note

The reference implementation in this repository remains open under the
charter (openness is a core principle). The binary + hardware-key
delivery terms describe the commercial distribution channel, not this
repo.
