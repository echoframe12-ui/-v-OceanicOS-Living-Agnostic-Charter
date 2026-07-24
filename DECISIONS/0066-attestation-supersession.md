# 0066 — Attestation Supersession

## Context

The attestation ledger is append-only by design: a record is never edited or
deleted, which is what makes the hash chain trustworthy. But real artifacts are
revised, and a later attestation often re-verifies a new version of what an
earlier one covered. Subject history (`DECISIONS/0046`) groups attestations by
name over time, which is a good *implicit* view — but it cannot answer the precise
question a consumer of an evolving artifact actually asks: *is this attestation the
current verified version, or has it been superseded by a newer one?* Nothing in
the record expressed the replacement link explicitly.

## Decision

Record supersession as an explicit, append-only link.

- A new `supersession.py` (`SupersessionLog`, its own table) records
  `new_id supersedes old_id` with an actor and a required reason. It never touches
  the attestation chain — a supersession is a claim *about* the record, kept beside
  it, exactly as the held-review and drift-audit logs are.
- `POST /attestations/<new_id>/supersedes` (`{old_id, reason}`, authed) records the
  link after validating both attestations exist, differ, a reason is given, and the
  exact link is not already recorded. `GET /attestations/<id>/lineage` returns what
  an attestation `supersedes`, what it is `superseded_by`, and `is_current` — true
  when nothing supersedes it.

## Consequences

- The record can now answer "is this current?": verified live, three
  re-verifications of a charter linked `#1 → #2 → #3` report `#3` as the sole
  `is_current` attestation with `#1` and `#2` superseded, each carrying its
  supersedes / superseded-by links — a version lineage the ledger states rather
  than one a consumer has to infer.
- It is deliberately separate from the chain and from subject history. The chain
  proves the record is untampered; subject history is the fuzzy by-name timeline;
  this is the precise by-id replacement graph. An artifact's supersession chain can
  cross subjects (a renamed file) or sit within one, because the link is on the
  attestations, not their names.
- Append-only and non-destructive: superseding an attestation neither edits nor
  hides it — the old attestation remains on the chain, verifiable and receipted, and
  simply reports `is_current: false`. The history of what *was* verified is never
  rewritten, only annotated with what replaced it.
- The link is validated but not further interpreted: the platform records that a
  steward asserted `#3` re-verifies `#1`'s artifact and why, and refuses a
  self-link or a duplicate. Whether the new attestation is a *better* verification
  is the confidence and dissent signals' job, not the supersession link's.
