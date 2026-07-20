"""A deterministic rules engine — the panel's fourth voice, and the only one
that explains itself.

The dissent panel's three model adapters are heuristics: they return a verdict
but not a reason. The manifest specifies "3 competing LLMs + 1 rules engine";
this is that rules engine. It is not another opaque strategy — it is a set of
named, inspectable rules, each with the reason it exists. When it votes to
revise, it says exactly which rules fired and why. Deterministic policy sitting
beside probabilistic judgement: the anchor of the panel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

APPROVE = "approve"
REVISE = "revise"


@dataclass(frozen=True)
class Rule:
    """One inspectable policy: a name, the reason it exists, and its test.

    `triggers_revise(prompt)` returns True when the prompt violates the rule —
    a reason to withhold approval, surfaced by name.
    """

    name: str
    reason: str
    triggers_revise: Callable[[str], bool]


def _no_actionable_verb(prompt: str) -> bool:
    verbs = ("plan", "build", "ship", "design", "attest", "verify", "review", "write", "draft")
    return not any(verb in prompt.lower() for verb in verbs)


def _unbounded_scope(prompt: str) -> bool:
    markers = ("everything", "all repos", "any and all", "literally any", "no limits")
    return any(marker in prompt.lower() for marker in markers)


def _long_without_context(prompt: str) -> bool:
    return len(prompt.split()) > 12 and "context" not in prompt.lower()


DEFAULT_RULES: list[Rule] = [
    Rule("empty", "an empty prompt has nothing to verify", lambda p: not p.strip()),
    Rule("no_actionable_verb", "no build verb — unclear what to produce", _no_actionable_verb),
    Rule("unbounded_scope", "unbounded scope ('everything'/'any') is unverifiable", _unbounded_scope),
    Rule("long_without_context", "a long prompt with no stated context is ambiguous", _long_without_context),
]


class RulesEngine:
    """Evaluate a prompt against a set of named rules, explainably.

    Returns the verdict *and* which rules fired and why — the panel member you
    can audit. Any fired rule is a reason to revise; a clean pass approves.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = list(rules) if rules is not None else list(DEFAULT_RULES)

    def evaluate(self, prompt: str) -> dict[str, Any]:
        fired = [rule for rule in self.rules if rule.triggers_revise(prompt)]
        return {
            "verdict": REVISE if fired else APPROVE,
            "fired": [rule.name for rule in fired],
            "reasons": [rule.reason for rule in fired],
            "rules_evaluated": len(self.rules),
        }


class RulesAdapter:
    """Wrap a `RulesEngine` as a panel member with the `ModelAdapter` interface.

    `matches` is always True: the rules engine weighs in on every prompt — it is
    the deterministic anchor that always sits on the panel, not a keyword match.
    Its `generate` carries the fired rules and reasons through `route_all`'s
    results, so the panel's dissent is explainable, not just counted.
    """

    # The rules engine anchors panels but is never the sole primary route:
    # ModelRouter.route() skips panel_only members.
    panel_only = True

    def __init__(self, engine: RulesEngine | None = None, name: str = "rules-engine") -> None:
        self.name = name
        self.provider = "rules-engine"
        self.keywords: list[str] = []
        self.engine = engine or RulesEngine()

    def verdict(self, prompt: str) -> str:
        return self.engine.evaluate(prompt)["verdict"]

    def matches(self, prompt: str) -> bool:
        return True

    def generate(self, prompt: str) -> dict[str, Any]:
        evaluation = self.engine.evaluate(prompt)
        return {
            "adapter": self.name,
            "provider": self.provider,
            "prompt": prompt,
            "verdict": evaluation["verdict"],
            "rules_fired": evaluation["fired"],
            "reasons": evaluation["reasons"],
        }

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "provider": self.provider, "keywords": []}
