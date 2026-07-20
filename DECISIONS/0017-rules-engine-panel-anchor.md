# 0017 — A Rules Engine as the Panel's Explainable Anchor

## Context

The manifest specifies the dissent panel as "3 competing LLMs + 1 rules engine,"
but the panel had only the three model adapters — keyword heuristics that return
a verdict and nothing else. Two gaps followed: there was no rules engine, and the
panel's dissent was counted but never *explained*. A verification platform whose
own panel can't say why it withheld approval is asking to be taken on faith.

## Decision

Add a deterministic, self-explaining rules engine as a fourth panel member.

- `rules.py` holds `Rule` (name + reason + test), a `RulesEngine` whose
  `evaluate()` returns the verdict **and** which named rules fired and why, and a
  default ruleset (empty prompt, no actionable verb, unbounded scope, long
  without stated context). Unlike the model heuristics, every revise is
  accountable to a named rule with a stated reason.
- `RulesAdapter` wraps the engine in the `ModelAdapter` interface so it joins
  `route_all`, carrying `rules_fired`/`reasons` through the panel results. It
  `matches` every prompt — it is the deterministic anchor that always sits, not
  a keyword match.
- It is `panel_only`: `ModelRouter.route()` skips panel-only members, so the
  rules engine anchors consensus but is never the sole primary route. The panel
  endpoints and the builder convene a panel of 4 (the three heuristics + the
  anchor); `route()` still returns a model adapter.
- `POST /rules/evaluate` exposes the explainable verdict directly.

## Consequences

- The panel is now "3 + 1" as specified, and its dissent is auditable: a revise
  names the rule and its reason. Verified live — `build everything` returns
  `revise` with `unbounded_scope` and its reason; a clean, contextful prompt
  approves with nothing fired; `/models/consensus` seats `rules-engine` as the
  fourth voice.
- Deterministic policy sits beside probabilistic judgement. The rules engine is
  the reproducible floor of the panel — it votes the same way every time, so
  disagreement between it and the heuristics is signal, not noise, and it folds
  into the consensus-weighted attestation confidence (DECISIONS/0008) like any
  other verdict.
- `panel_only` is a general seam: any future member that should weigh in on
  panels without being a primary route reuses it, and `route()`'s fallback also
  respects it, so a panel-only adapter registered first still never answers
  alone.
- The default ruleset is intentionally small and inspectable; `RulesEngine`
  takes a custom `rules` list, so a deployment can encode its own policy without
  touching the panel wiring.
