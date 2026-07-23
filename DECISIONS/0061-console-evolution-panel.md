# 0061 — Console Evolution Panel

## Context

Round 60 (`DECISIONS/0060`) added `GET /evolution`, the platform's compounding
footprint — a count per append-only ledger and a running total. But it lived only
in the API. The console, the operator's face, could show every trust *signal* yet
said nothing about how much the platform had *accrued*. The compounding the
Doctrine names as its final-state invariant was invisible where an operator
actually watches the system.

## Decision

Surface the footprint as an `Evolution // Compounding` panel.

- The panel loads `/evolution` and shows the headline — `N records across M
  append-only ledgers · the histories compound` — above a compact table of each
  ledger's count and what it accrues, in a fixed, legible order.
- It hydrates on page load with the other public panels, so the footprint is
  present without any action.

## Consequences

- The invariant is now legible in the terminal: verified live in a browser, the
  panel reads `65 records across 8 append-only ledgers`, with the decision log the
  largest ledger at 60 — the operator sees, at a glance, that the biggest thing
  the platform has accumulated is the record of its own evolution.
- Presentation only, a thin client over the round-60 endpoint — no new state, no
  UI-side computation (the server counts; the console renders), the same console
  discipline held throughout (`DECISIONS/0034`). The `/` route still renders and
  every other panel loads.
- Zero-count ledgers are shown, not hidden: a fresh deployment reads all eight at
  `0`, which is the honest starting point of compounding — the ledgers exist and
  are empty, ready to grow, rather than absent.
- With this the console now has a home for every layer the platform reports: the
  four trust dimensions (confidence, integrity, evidence, dissent), the trust
  posture (Integrity panel), the record itself (Search, Receipt, Timeline), and
  now the compounding footprint — the operator can read the whole system from the
  one terminal.
