# 0020 — Prometheus Metrics Endpoint

## Context

The platform is pitched as deployable, but everything an operator would monitor —
CVI, the held queue, SLA breaches, chain integrity — was reachable only as
scattered JSON across `/cvi`, `/admin/overview`, and `/attestations/verify`. A
real deployment is scraped by a monitoring stack (Prometheus, Grafana, and the
long tail of tools that speak its format), and there was nothing for them to
scrape. Observability that requires a bespoke integration is observability most
operators won't wire up.

## Decision

Expose platform state at `GET /metrics` in the Prometheus text exposition format.

- `metrics.py` is a pure renderer: `render([{name, help, value, type?}])` emits
  the `# HELP` / `# TYPE` / sample lines, with `gauge` the default type and
  booleans rendered as `1`/`0`. It formats; it does not collect.
- `app.py` assembles the live snapshot from the components already computing
  these numbers — `attestation_engine` (totals, held, CVI, chain verify),
  `held_review_log` (pending, SLA breaches), `service`, `auth_registry`,
  `model_router` — and serves it with the standard content type.
- The endpoint is **public**, like `/cvi`: it exposes only aggregate scalars,
  never per-actor content, so it carries nothing that `/admin/overview`'s gating
  protects. Prometheus scrapers are typically unauthenticated within a network;
  gating would just break the common case for no privacy gain here.

## Consequences

- OceanicOS is now observable by ordinary tooling with zero custom code: point a
  scraper at `/metrics`. Verified live — a running server reports real series
  (`oceanicos_attestations_total 3`, `oceanicos_cvi 0.533`,
  `oceanicos_chain_intact 1`, `oceanicos_model_adapters 4`) in valid exposition
  format with the correct `text/plain; version=0.0.4; charset=utf-8` type.
- The security posture is deliberate and narrow: aggregate counts only. If a
  deployment considers even counts sensitive, the endpoint is a single
  `require_admin` away from gated — but the default matches the ecosystem's
  expectation and `/cvi`'s existing public stance.
- All gauges, no counters: these are current readings of a live record, not
  monotonic event totals, so a gauge is the honest type. If a genuine
  monotonic counter is ever added (e.g. total quota blocks), the renderer
  already carries per-metric `type`.
- The renderer is decoupled from collection, so new series are one dict in the
  snapshot list — no format code changes as the platform grows.
