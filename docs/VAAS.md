# Verification-as-a-Service (VaaS)

The trust/latency arbitrage, productized. OceanicOS occupies the gap
between instant generation and validated output: every deliverable is
attested (hash, confidence, source trail), dissent between models is
surfaced rather than hidden, below-threshold work is held for a human,
and the ledger degrades gracefully to CSV and plain text.

The 4-second render delay is not a limitation. It is the product — the
computational cost of verification, made visible.

## Tiers (USD / month)

| Tier | Price | Build quota | Includes |
| --- | --- | --- | --- |
| **Attestor** | $8,500 | 10 builds / hour | Attestation API, Composite Verification Index (CVI), CSV/.txt ledger exports |
| **Arbiter** | $25,500 | 50 builds / hour | Everything in Attestor + 3-model + rules-engine dissent panels, held-review SLAs |
| **Sovereign** | $85,000 | unlimited | Everything in Arbiter + on-prem binary distribution, hardware-key (YubiKey) handoff, no source escrow |

The Arbiter **held-review SLA** is a real workflow, not a promise: a steward
reviews attestations held below the 0.74 threshold and records a `release` or
`uphold` with a reason (`GET /attestations/held`, `POST
/attestations/<id>/review`). Reviews are append-only — the held attestation is
never rewritten, so the tamper-evident chain stays intact — and a documented
release lifts the item out of the CVI's held ratio. The SLA is timed: held items
age against `OCEANICOS_HELD_SLA_SECONDS` (default 24h), pending items flag
`sla_breached`, and `/admin/overview` reports `held_sla_breached`. See
[DECISIONS/0018](../DECISIONS/0018-held-review-workflow.md) and
[DECISIONS/0019](../DECISIONS/0019-held-review-sla-aging.md).

Live tier data: `GET /pricing`. The quota is a **rolling rate limit** enforced
per named account (`GET /me/quota` reports `used`, `window_seconds`, and
`resets_at`); usage recovers continuously as builds age out of the window. The
window is configurable via `OCEANICOS_QUOTA_WINDOW` (default 3600s). An admin
assigns tiers (`POST /admin/users/<username>/tier`). See
[DECISIONS/0005](../DECISIONS/0005-per-tier-quotas.md) and
[DECISIONS/0009](../DECISIONS/0009-windowed-rate-limits.md).

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
