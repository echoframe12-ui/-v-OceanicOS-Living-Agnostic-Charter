# 0054 — Offline Status-Digest CLI

## Context

Round 53 (`DECISIONS/0053`) made the platform's posture provable — `GET
/status/digest` signs a canonical snapshot with the operator key. But only the
*producing* half existed, and only inside the running service. The ledger has a
complete portable loop — `export` a bundle, verify it anywhere with
`verify_ledger.py`, no service required — while the digest could be produced only
by a live server and verified only by importing a Python function. The "hand it to
an auditor who runs one command" step, and the ability to emit a digest offline
from a ledger, were both missing.

## Decision

Add a `digest` subcommand to the `oceanic_os.py` CLI, and share the payload
construction so the CLI and the endpoint cannot diverge.

- `status_digest.posture_of(verify)` and `status_digest.build_payload(...)` now
  hold the single definition of the verdict and the signable payload. The
  `/status/digest` endpoint and the `_status_snapshot` posture were refactored to
  call them, so there is one source for both.
- `oceanic_os.py digest` builds a signed digest from the configured ledger — the
  same `build_payload`, signed with `OCEANICOS_SIGNING_KEY` — and prints it for
  archival. `oceanic_os.py digest --verify FILE` (or `-` for stdin) checks a
  digest's signature and exits non-zero if it does not verify.
- Held-queue health used by both `gate` and `digest` was factored into one
  `_held_health` helper, computed exactly as the service does.

## Consequences

- The self-report loop is now complete and service-free: verified live, the CLI
  emits a signed digest (`posture TRUSTWORTHY`, `signed true`), an auditor runs
  `digest --verify` and gets `VALID` (exit 0), a wrong key gives `INVALID` (exit
  1), and a tampered posture fails — the same portability the ledger already had,
  now for the platform's own health.
- Producer parity is structural, not hoped-for: because the endpoint and the CLI
  both call `build_payload`, a digest produced by the running service and one
  produced offline from the same ledger agree on every signable field — verified
  live, all nine (excluding the timestamp) match. A digest cannot mean one thing
  from the server and another from the CLI.
- The refactor removed a real duplication risk: the posture verdict and the
  held-health computation each now live in one place, so the status board, the
  JSON twin, the signed digest, the gate, and the CLI can never disagree about
  what the posture *is* or how the held queue is counted.
- `--verify` takes the key from `--key` or the environment, mirroring
  `verify_ledger.py`, so the two offline verifiers — one for the ledger, one for
  the posture — present the same interface to a CI job or an auditor.
