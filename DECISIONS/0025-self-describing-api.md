# 0025 — Self-Describing API (generated OpenAPI)

## Context

`app.py` grew to 65 routes across fifteen rounds, while `API_SPEC.md` — written
by hand — still described only the original health/plans/memory/tools surface.
Every new endpoint widened the gap, and any hand-maintained spec would keep
drifting the moment the next route landed. A spec that lies is worse than none:
clients trust it. The routes themselves are the only thing that can't be wrong.

## Decision

Generate the API spec from the live route table.

- `openapi.py`'s `generate(url_map, view_functions, ...)` is a pure function over
  Werkzeug's route map. It documents every route (bar `static`): the path
  (`<int:att_id>` → `{att_id}`), the methods (minus `HEAD`/`OPTIONS`), a summary
  taken from the view's docstring, and typed path parameters (`int`→integer,
  `float`→number, else string). It returns a valid OpenAPI 3.0.3 document.
- `GET /openapi.json` serves it, public like the other read surfaces, and it
  documents itself among the paths.
- `API_SPEC.md` keeps the conceptual prose but points at `/openapi.json` as the
  authoritative, always-current surface.

## Consequences

- The spec is accurate by construction and cannot drift: it is derived from the
  same routes it describes, so a new endpoint appears the instant it is
  registered, with no annotation to remember. Verified live — the generated doc
  lists 58 paths, types `att_id` as an integer path param, and includes every
  round's endpoints (`/metrics`, `/cvi/history`, `/rules/evaluate`,
  `/attestations/checkpoint`, …) with summaries lifted from the docstrings, all
  without a hand edit.
- Scope is deliberately the *surface*, not the schemas: paths, methods,
  summaries, and path parameters — not request/response bodies. Drift of the
  endpoint list was the real problem; body schemas are a later, additive step
  (the generator returns a place to hang them). A minimal spec that is always
  true beats a rich one that rots.
- Summaries come from docstrings the code already carries, so documentation
  quality tracks the code's own self-description — another reason to keep view
  docstrings meaningful.
- Zero new dependency: it walks the `url_map` Flask already builds. The
  generator takes the map and views (not the app), so it is unit-tested in
  isolation and could describe any Flask app.
