# 0007 — Real Dissent

## Context

The friction protocol's flagship claim is "run competing models and surface the
dissent as the primary output." But the dissent panel was cosmetic: every demo
adapter returned the same result shape differing only by its own name, so
`route_all` computed `dissent` by diffing whole result dicts — which always
differ because the adapter name is in them. Dissent was structurally
guaranteed and therefore meaningless.

## Decision

Move dissent from **identity** to **verdict**.

- Each adapter carries a `strategy` — a deterministic heuristic that returns a
  verdict (`approve` / `revise`) from the prompt. Three demo strategies with
  genuinely different biases: `optimist` (approves forward intent),
  `skeptic` (approves only with evidence), `literal` (approves only short,
  unambiguous prompts).
- `generate()` includes the `verdict`. `route_all` now reports `verdicts`, the
  `distribution`, the `majority`, and computes `dissent` as *more than one
  distinct verdict* — so agreement is possible and disagreement is real.
- Adapters without a strategy (e.g. the real `ClaudeAdapter`, whose output is
  its content) return `abstain`; they don't manufacture false dissent.

## Consequences

- The panel now genuinely agrees or disagrees depending on the prompt:
  "Plan the build" splits optimist(approve)/skeptic(revise); "Plan the verified
  build" reaches consensus. The output carries the majority and the split.
- The heuristics are honest demo stand-ins, not real models — but the *shape*
  of the feature is now correct, so wiring in real adapters (each returning a
  verdict) produces meaningful dissent without further plumbing.
- "Certainty is a bug" is now demonstrable: the platform can show a real split
  rather than a guaranteed one.
