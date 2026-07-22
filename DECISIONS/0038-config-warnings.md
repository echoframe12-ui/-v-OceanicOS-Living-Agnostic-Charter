# 0038 — Operational Config Warnings

## Context

Round 33 (DECISIONS/0027) exposed the effective config at `/config`, but reading
a value is not the same as knowing whether it is *safe*. Several combinations
degrade a feature silently: a signing key set with no auto-checkpoint cadence
(the head is almost never sealed), no admin users (held attestations can never be
reviewed), signing off entirely (no tamper-resistance). An operator sees the
numbers but not the risk they carry.

## Decision

Compute warnings from the effective config and surface them at `/config`.

- `_config_warnings(cfg)` is a pure function over the effective config, returning
  `{level, message}` findings: `warn` for a gap that undermines a feature the
  operator evidently wants (signing on but auto-seal off; no admins), `info` for
  a deliberate-but-notable posture (no signing key; auth enforcement off; SLA
  disabled). It reads the config's shape, never a secret.
- `/config` includes a `warnings` list alongside the config it evaluates.

## Consequences

- Misconfiguration stops being silent: verified live — a no-key, auth-off
  instance reports the two `info` findings, and a healthy instance (key +
  auto-seal + admins + auth) reports **no warnings at all**. The absence of
  warnings is itself the signal that the deployment is sound.
- The distinction between `warn` and `info` is deliberate and load-bearing:
  `warn` marks an *inconsistency* — a feature switched on but left ineffective
  (signing without sealing) — while `info` marks a coherent choice worth stating
  (running open and unmetered on purpose). A tool or a human can gate on `warn`
  without being nagged by `info`.
- It is pure and separate from the endpoint, so the rules are unit-tested
  directly against synthetic configs, and the same function could feed a CLI
  `doctor` check later without touching the HTTP layer.
- No secret enters the warnings: they are derived from the same booleans and
  counts `/config` already reports (`signing_enabled`, `admins`, the checkpoint
  policy), so the safety net inherits the config endpoint's secret hygiene.
