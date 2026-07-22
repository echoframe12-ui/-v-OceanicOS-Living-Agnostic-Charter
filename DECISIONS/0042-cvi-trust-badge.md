# 0042 — CVI Trust Badge

## Context

The Composite Verification Index is the platform's headline trust signal, but it
lived only where someone was already looking — the `/cvi` JSON, the console's
Integrity panel, the Prometheus scrape. The one surface a prospective user sees
first, the repository page itself, said nothing about how trustworthy the record
currently is. A README can embed an image; it cannot embed a JSON call. The trust
index needed a form that renders on a page it does not control.

## Decision

Serve the live CVI as an embeddable SVG badge at `GET /badge/cvi.svg`.

- A new pure module `badge.py` renders a flat two-cell SVG — grey
  `verification` label, coloured value — with no external service (not
  shields.io), no network, and no embedded fonts: width is approximated from the
  character count so the SVG is deterministic and cache-stable.
- The colour is threshold-aligned. `cvi_color` maps the index to green at or
  above the platform's `0.74` held/attested line (`DECISIONS/0001`), yellow for a
  near-miss, then orange and red below — so a badge pinned to the repo reads the
  same truth the terminal does, and can only be green when the record earns it.
  Out-of-range values clamp; a non-numeric index yields grey rather than an error.
- The endpoint reads the same `cvi()` the `/cvi` route does (released items
  credited), is public and aggregate like `/cvi`, honours `?label=`, and is sent
  `Cache-Control: no-cache` so an embed shows the current index, not a stale one.

## Consequences

- The trust index is now portable to any page that renders an image. The record's
  self-reported trustworthiness travels with the repository, not just the running
  service — the same instinct as the offline verifier and the exportable bundle
  (`DECISIONS/0013`): the proof should survive the context it was made in.
- Verified live: an empty ledger renders `0.00` in red; five 0.9 attestations
  render `0.90` in green; the label override and the SVG's accessible
  `aria-label`/`<title>` both carry through. The colour flips at the same 0.74
  the rest of the platform holds.
- Presentation only, a thin read over `cvi()` with no new state — the console
  discipline (`DECISIONS/0034`) extended to a surface outside the console. The
  badge restates the index; it never computes a second one that could disagree.
- The badge tells the truth even when the truth is unflattering: a low or empty
  record shows red, not a hidden failure. That is the point — a trust badge that
  could only be green would be the false certainty this platform refuses.
