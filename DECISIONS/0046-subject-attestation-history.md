# 0046 — Per-Subject Attestation History

## Context

The ledger could find attestations two ways: by actor (`list(actor=…)`) and by
exact content hash (`by_content_hash` / `/attestations/lookup`). Both are useful,
but neither answers a question a verification platform is squarely about: *how has
trust in this one artifact moved over time?* Content-hash lookup groups identical
*bytes* — the moment an artifact is revised, its hash changes and the new
attestation no longer joins the old one. There was no way to follow a single
logical artifact across its versions and see whether it was re-verified, and
whether its confidence was trending up or down.

## Decision

Add a per-subject timeline keyed on logical identity, not bytes.

- `AttestationEngine.subject_history(subject)` returns every attestation carrying
  that exact `subject`, oldest to newest, plus a small trend summary: `count`,
  `reverified` (more than one), `ever_held`, `first_confidence`,
  `latest_confidence`, `confidence_delta`, and `latest_status`. A subject with no
  attestations returns a well-formed zero-count summary rather than an error.
- `GET /attestations/history?subject=…` exposes it — public and aggregate like
  the content-hash lookup it complements; 400 without a subject, 200 with a
  zero-count body for an unknown one.

## Consequences

- The platform can now tell an artifact's trust *story*, not just its current
  state: verified live, a charter draft attested three times as it was revised
  reads `held 0.42 → held 0.71 → attested 0.93`, a `confidence_delta` of `+0.51`,
  `ever_held` true, `latest_status` attested. That progression — first held, then
  earned — is exactly the "validated hesitation" the platform sells, made visible
  over time for a single subject.
- It is the logical-identity companion to content-addressable lookup, and the
  per-subject companion to the platform-wide CVI history (`DECISIONS/0023`): one
  is the global trend, this is the trend for one artifact. Three complementary
  axes onto the same record — by bytes, by name, by whole-ledger index.
- Read-only over the existing record: `subject_history` is one `_rows` query and
  a fold, no new state and no schema change, so it cannot disagree with the
  attestations it summarises and needed no migration.
- Exact-match, not substring: `search(subject_contains=…)` already offers fuzzy
  discovery; this is deliberately the precise timeline for one known subject, so
  the trend is of that artifact and not an accidental grouping of similarly-named
  ones.
