# 0034 — Console Surfaces the Newer Endpoints

## Context

The interactive console (DECISIONS/0022) was built at round 28, but the platform
kept growing: aggregate stats (0032), per-attestation receipts (0033), and the
served decision log (0031) all landed after it. The API could do things the
console couldn't show — the product's face had fallen behind its capabilities,
which is its own kind of drift.

## Decision

Bring the console back up to the API surface with three additions, all thin
clients over existing endpoints:

- **Ledger Stats** — a totals line and a confidence histogram (horizontal bars,
  the ≥0.75 bucket in the attested colour, the rest held) plus the per-actor
  breakdown, from `/attestations/stats`; refreshed with the dashboard.
- **Receipt // Proof** — an id lookup that fetches `/attestations/<id>/receipt`
  and shows the hash, chain position, integrity, and whether it is `SEALED`.
- **Governance // ADR** — the decision log from `/adr`, each record a link that
  loads its full text from `/adr/<n>` inline.

## Consequences

- The console again reflects what the platform can do: verified live — the stats
  panel renders the histogram and by-actor counts, the receipt panel resolves an
  attestation to its proof, and the ADR browser lists every record and opens one
  on click.
- Presentation only, no new endpoint or state — each panel is a direct client of
  an endpoint the tests and CLI already exercise, so there is no divergent logic
  to keep in sync, only markup.
- The same discipline as the generated OpenAPI (0025) and the served ADRs (0031),
  applied to the UI: the interface is a view of the API, kept honest by reading
  from it rather than restating it. Output is escaped before insertion, matching
  the rest of the console.
