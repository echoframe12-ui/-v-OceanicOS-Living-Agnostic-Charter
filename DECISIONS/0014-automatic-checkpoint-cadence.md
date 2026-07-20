# 0014 — Automatic Checkpoint Cadence

## Context

Round 12 (DECISIONS/0012) gave the ledger signed checkpoints — the defense that
catches a wholesale rewrite. But the only way to take one was an admin calling
`POST /attestations/checkpoint`. In practice that means the head is almost never
sealed: the record grows, unsigned, between the rare manual checkpoints, and
everything attested in that gap is protected only by the tamper-*evident* chain,
not the tamper-*resistant* seal. A security control that depends on a human
remembering to run it is a security control that mostly isn't running.

## Decision

Let the engine seal itself on a cadence.

- `OCEANICOS_CHECKPOINT_EVERY` (constructor `checkpoint_every`, default 0) sets
  how many new attestations may accrue before the head is auto-sealed. 0 keeps
  the round-12 behavior exactly — manual-only. Any positive N means "seal every
  N attestations."
- After each `attest()` commits (and its transaction is closed), the engine
  checks how many entries have landed since the last checkpoint and seals if the
  cadence is reached. It runs only when both a cadence and a signing key are set.
- The auto-seal is best-effort: a failure (e.g. a transient lock) is swallowed
  so it can never fail the attestation it follows — the record is the priority,
  and the next attest retries. Manual `POST /attestations/checkpoint` still works
  and composes (both write to the same checkpoint table; the latest wins).
- `checkpoint_policy` (`{can_sign, auto, every}`) is surfaced in
  `/admin/overview` so an operator can see whether the head is being sealed and
  how often.

## Consequences

- The signed guarantee now actually operates. A deployment that sets a key and a
  cadence gets a continuously-sealed head with no human in the loop — verified
  live: three builds through a two-worker service auto-sealed and reported
  `trustworthy: true` with no manual checkpoint call.
- The window of unsigned exposure is bounded by the cadence, and it's the
  operator's dial: tighter N (more seals, more writes) versus looser N (fewer
  writes, a larger trailing unsigned tail). One hour of builds or every handful
  of attestations — the deployment chooses.
- Backward compatible: the default of 0 leaves existing behavior and every
  existing test unchanged. Auto-sealing is opt-in, and silently inert without a
  key, so nothing gains a false sense of protection it isn't configured for.
- Concurrency is harmless: if two workers both cross the boundary they may each
  seal, producing two adjacent checkpoints — the latest is authoritative and the
  offline verifier already reads the last one.
