# 0036 — Operator CLI Subcommands

## Context

`oceanic_os.py` could boot the stack and report it (DECISIONS/0015), but that was
all it did. Meanwhile the platform had grown pure, service-free primitives —
`AttestationEngine.verify()` / `.stats()` and `readiness.probe()` — that an
operator would want at the command line: check the ledger, read its shape, probe
readiness, without standing up the HTTP server or writing a client. The
capability existed; the CLI didn't expose it.

## Decision

Turn the boot CLI into a small operator tool with subcommands.

- `main` dispatches on a leading command word: `boot` (the default), `verify`,
  `stats`, `ready`. A leading flag or no argument still runs `boot`, so the
  original `oceanic-os --boot …` invocation is unchanged and back-compatible.
- Each subcommand instantiates the relevant pure component against the configured
  `OCEANICOS_DB` / `OCEANICOS_WORKSPACE` and prints a one-line summary (or `--json`
  for the raw report): `verify` walks the chain and **exits non-zero if broken**;
  `stats` prints the aggregate; `ready` probes the operational dependencies and
  **exits non-zero if not ready**. An unknown command exits 2.

## Consequences

- The ledger is operable from the shell, offline: verified live — `verify` prints
  `chain: INTACT · length 2 · trustworthy` (exit 0), `stats` prints
  `attestations: 2 (1 attested, 1 held, ratio 0.5)`, `ready` prints the checks,
  `boot` still works as the default, and an unknown command exits 2. Meaningful
  exit codes make `verify`/`ready` usable in a cron or CI gate.
- Reuse, not reimplementation: each subcommand is a thin wrapper over the same
  `verify`/`stats`/`probe` the HTTP endpoints call, so the CLI and the API can't
  give different answers — one source, two front doors.
- It extends the "survives without the system" line the boot CLI and the offline
  verifier established: operating and checking the platform never requires the
  web layer to be up.
- Back-compatibility was a hard constraint, not an afterthought: the dispatcher
  treats a leading flag as the `boot` path precisely so every existing caller and
  test of `oceanic-os --boot …` keeps working unchanged.
