# 0065 — Human Trust Report

## Context

The platform reports its state richly, but only for machines and operators:
`/status.json` is a JSON posture, `/metrics` is a scrape, `/evolution` is a
counts object, the console is an interactive terminal. None of these is something
you hand to a stakeholder, attach to a release, or drop into a report — a person
who wants "how is the verification layer doing?" as one readable page had to
assemble it themselves from several endpoints.

## Decision

Add `GET /report` — a composed, human-readable Markdown trust report.

- A new pure `report.py` (`render`) takes the assembled structures — the status
  snapshot, the compounding footprint, and the dissent stats — and formats them
  into one page: the posture verdict, a signal table (chain, CVI with its
  confidence spread and peak, source coverage, dissent, held queue, latest
  checkpoint and drift audit), and the compounding footprint.
- The endpoint gathers those from the same reads the machine surfaces use — a new
  `_ledger_counts()` helper is now shared by `/evolution` and `/report` so the two
  cannot disagree — and returns `text/markdown`.

## Consequences

- The platform's whole state is now one document a person can read: verified live,
  the report renders the posture (`TRUSTWORTHY`), every trust dimension, the seal
  and last audit, and the footprint (`71 records across 8 append-only ledgers`) —
  the Markdown counterpart to `/status.json`, for the human instead of the monitor.
- It states no new fact and keeps no state: `render` is a pure formatter over
  structures the surfaces already produce, and the shared `_ledger_counts()` means
  the report's footprint is the same numbers `/evolution` serves. The report can
  never say something the machine surfaces contradict.
- The CVI's bracket is labelled `confidence 0.61–0.94`, not shown as a bare range,
  because in a prose report a confidence spread whose low end sits above the
  held-discounted CVI reads as an error otherwise. The label names what the
  interval is — the spread of the underlying confidences (`DECISIONS/0040`), not a
  range on the CVI — so the honest number is also the legible one.
- It renders the same honesty the board does: a `TRUSTWORTHY` chain can appear
  beside a middling CVI, and a broken chain renders `BROKEN at #id` with `none
  sealed yet` — the report does not flatter the record, which is the point of a
  report a stakeholder is meant to trust.
