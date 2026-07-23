# 0060 — The Compounding Footprint

## Context

The Doctrine's loop was extended to end *Recompile → **Compound***: memory
compounds, artifacts compound. And it is literally true of this platform — it
keeps not one record but eight append-only ledgers (attestations, checkpoints,
builds, drift audits, the CVI trend, held-review decisions, dissent evaluations,
and the decision log of its own evolution), each only ever growing. But that
accrual was invisible as a whole. You could read any one ledger; you could not
read *how much the system has accumulated* over its life — the compounding the
Doctrine names had no single figure.

## Decision

Report the compounding as data: `GET /evolution`.

- A new pure `evolution.py` (`compounding`) takes the per-ledger counts and
  structures them — each ledger with its count and a note on what it accrues, plus
  the `ledger_count` and a `records_total` across all of them, marked
  `append_only`.
- The endpoint gathers the counts from the live ledgers and returns the footprint.
  Public and aggregate like `/metrics`: counts only, never per-record content.
- The Doctrine's *Final State* layer now cites `/evolution` and the `evolution`
  module (and `DOCTRINE.md`'s loop gains the `COMPOUND` step), so the doctrine
  self-check verifies the compounding node points at real code.

## Consequences

- Compounding is now a figure you can read, not a claim: verified live, the
  platform reports `records_total 65` across `8` ledgers — 3 attestations, 1
  checkpoint, 1 drift audit, 1 dissent evaluation, and **59 decision records**,
  the rounds of the platform's own evolution. The largest ledger is the log of how
  it was built, which is exactly the point: *the method is the message*
  (`docs/POSITIONING.md`) made countable.
- Every counted ledger is append-only, so the footprint only grows — nothing here
  is rewritten. `append_only: true` is the honest claim behind the compounding:
  the histories accumulate, they are not edited, which is why they can compound at
  all.
- Composition, not new state: `compounding` is a pure fold over counts the
  ledgers already expose (`list()`, `list_checkpoints()`, `stats()`,
  `list_adr()`), so the footprint cannot disagree with the ledgers it sums, and it
  needed no new storage.
- On honesty about the self-evolving layer: the Doctrine's *mue-x / self-rewriting
  runtime* is external to this repository, like the physical security layer. What
  is shipped here is the compounding *record* of an evolution carried out with a
  verification trail — this endpoint measures that record, and does not claim a
  runtime agent the repo does not contain.
