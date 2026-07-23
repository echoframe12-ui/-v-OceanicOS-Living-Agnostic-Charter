# 0051 — Console: Source Coverage and Per-Entry Integrity

## Context

Two capabilities shipped on the API but never reached the operator console. Source
coverage (`sourced_ratio`, `DECISIONS/0048`) was surfaced on `/metrics`,
`/status.json`, and the public status board — but not in the console's own Stats
panel, which showed totals and confidence yet said nothing about evidence.
Per-entry integrity (`entry_intact`, `DECISIONS/0043`) was on the receipt payload,
but the console's Receipt panel reported only `chain_intact` — the whole-ledger
verdict — so an operator reading a receipt could not see whether *that specific
entry* was untampered. The console was a step behind the record it fronts.

## Decision

Surface both in the panels that already show their neighbours.

- The **Stats panel** gains a `sourced` row: the coverage percentage and the raw
  `sourced/total`, colour-banded on the same `0.74` line as the rest of the
  platform — the evidence axis beside the confidence mean it complements.
- The **Receipt panel** now distinguishes *this entry* from *the ledger*: it shows
  `this entry intact / TAMPERED` (from the receipt's `entry_intact`) alongside the
  existing `ledger ok / BROKEN` — so a receipt certifies its own entry visibly,
  not just the chain around it.

## Consequences

- The console now tells the same trust story its own API does: verified live in a
  browser, the Stats panel reads `SOURCED 67% (2/3 cite evidence)` and a receipt
  for entry #2 reads `chain 2/3 · this entry intact · ledger ok · SEALED` — the
  per-entry verdict and the source coverage both visible where an operator works.
- Presentation only, thin clients over fields the endpoints already return
  (`stats()["sourced_ratio"]`, the receipt's `entry_intact`) — no new state, no
  new server logic, and no possibility of the console disagreeing with the API it
  reads. The `/` route still renders and every panel still loads.
- The Receipt panel's wording is deliberate: "this entry" vs. "ledger" names the
  two distinct integrity questions the per-attestation verify made separable
  (`DECISIONS/0043`), so the operator sees which one a red result implicates.
- Closes the visible gap between the record and its face: the recently-added trust
  dimensions (evidence, per-entry integrity) are now legible in the console, not
  only in the machine surfaces.
