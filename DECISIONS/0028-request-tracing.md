# 0028 — Request Tracing and Structured Access Logs

## Context

Observability had two of its three legs: metrics (0020) and health/readiness
(0026). The third was missing — logs. A request left no trace: no id to
correlate a client's report ("this call failed at 14:03") with what the server
did, and no structured access record to feed a log pipeline. Debugging a
production incident meant guessing.

## Decision

Give every request a trace id and a structured access-log line.

- A `before_request` hook sets `g.request_id` (via `requestlog.clean_request_id`)
  and a start timestamp; an `after_request` hook echoes the id in the
  `X-Request-ID` response header and logs one JSON object — `request_id`,
  `method`, `path`, `status`, `actor`, `latency_ms` — to a dedicated
  `oceanicos.access` logger (its own stderr handler, `propagate=False`, so lines
  aren't duplicated through the root logger).
- The id is **accepted from the caller** (`X-Request-ID`) for cross-service trace
  propagation, or minted when absent — so a trace started upstream continues
  through this service.
- **The one place that trusts a caller-supplied header is sanitized.**
  `clean_request_id` strips the id to `[A-Za-z0-9._-]` and caps it at 64 chars;
  anything that sanitizes to empty gets a minted id. This closes log injection
  (newlines, control characters, spaces) by construction — the header flows into
  log lines, so it cannot be allowed to carry a forged line.

## Consequences

- Every response is traceable: verified live — a minted id and a propagated
  `trace-abc` both appear in the `X-Request-ID` header and in the JSON access
  line, and a header like `bad id|<x>` is sanitized to `badidx` before it is
  reflected or logged.
- The structured line is a real log-pipeline input (one JSON object per line),
  carrying the actor and latency, so requests are queryable by id, path, status,
  or user without parsing free text.
- Defense in depth on the trace header: Werkzeug already rejects newlines at the
  header layer, and the sanitizer removes everything else outside the safe set —
  so neither the framework's gap nor a non-Werkzeug caller can inject a log line.
- The pure helpers (`clean_request_id`, `access_record`) live in `requestlog.py`,
  not the hooks, so the security-sensitive sanitizing is small, isolated, and
  unit-tested directly; the hooks are thin glue.
