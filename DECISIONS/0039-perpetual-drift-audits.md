# 0039 — Perpetual Drift Audits

## Context

The Observer's architecture tree lists, under Security, "Perpetual Drift Audits,"
and it was the one node the platform only half-covered. The ledger is *verifiable*
on demand (`/attestations/verify`), but verifiable is not verified: nothing
recorded that a check ran, or its result over time. Drift is caught by looking,
and the platform kept no memory of ever having looked — so it could prove the
record *can* be checked, never that it *has been*, continuously.

## Decision

Give the platform a persistent memory of its own integrity checks.

- `drift_audit.py` (`DriftAuditLog`, mirroring `usage.py`) persists each
  `verify()` result to a `drift_audits` table (`intact, trustworthy, length,
  broken_at, checked_at`); `list()` returns history newest-first, `latest()` the
  most recent.
- `POST /attestations/audit` (admin) runs a verify and records it — a drift audit
  on demand, a stewardship action. `GET /attestations/audits` (`?limit=`) is the
  trail, public like `/attestations/verify`.
- Sealing a checkpoint also records an audit, so the head being signed leaves an
  audit point without a separate call — continuous validation tied to the moment
  it matters most.
- `/metrics` gains `oceanicos_last_audit_intact` (1 when the latest audit was
  intact or none has run, 0 when the last one found a break), so a monitor can
  alert on a drift audit that came back broken.

## Consequences

- Verifiable becomes verified-and-remembered: verified live — a manual audit
  records `intact: true`, sealing a checkpoint auto-appends a second audit, and
  after a direct tamper an audit records `intact: false, broken_at: 1` while
  `oceanicos_last_audit_intact` flips from `1` to `0`. The trail is the evidence
  the record was watched, not merely watchable.
- The audit is a read of the same `verify()` the endpoint and CLI use, so an
  audit entry and a live verify agree by construction; the trail adds history,
  not a second notion of integrity.
- Recording at each checkpoint makes the audit cadence follow the sealing cadence
  (`OCEANICOS_CHECKPOINT_EVERY`): a deployment that auto-seals also auto-audits,
  so "perpetual" is a configuration away, not a cron to bolt on.
- The metric's default (1 when no audit has run) is deliberate: absence of a
  known break is not an alert. It flips to 0 only on a recorded break, so the
  alert fires on evidence of drift, not on silence.
