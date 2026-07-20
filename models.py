from __future__ import annotations

from collections import Counter
from typing import Any, Callable

# Verdict strategies — distinct heuristics so a dissent panel produces real
# disagreement, not structural echoes. Each returns "approve" or "revise".

APPROVE = "approve"
REVISE = "revise"


def strategy_optimist(prompt: str) -> str:
    """Approves when it reads forward intent in the prompt."""
    lowered = prompt.lower()
    return APPROVE if any(k in lowered for k in ("plan", "build", "ship", "design")) else REVISE


def strategy_skeptic(prompt: str) -> str:
    """Withholds approval unless the prompt shows evidence."""
    lowered = prompt.lower()
    return APPROVE if any(k in lowered for k in ("verified", "attested", "evidence")) else REVISE


def strategy_literal(prompt: str) -> str:
    """Approves only short, unambiguous prompts."""
    return APPROVE if len(prompt.split()) <= 4 else REVISE


class ModelAdapter:
    def __init__(
        self,
        name: str,
        provider: str,
        keywords: list[str] | None = None,
        strategy: Callable[[str], str] | None = None,
    ) -> None:
        self.name = name
        self.provider = provider
        self.keywords = [keyword.lower() for keyword in (keywords or [])]
        self.strategy = strategy

    def verdict(self, prompt: str) -> str:
        return self.strategy(prompt) if self.strategy else "abstain"

    def generate(self, prompt: str) -> dict[str, Any]:
        return {
            "adapter": self.name,
            "provider": self.provider,
            "prompt": prompt,
            "verdict": self.verdict(prompt),
        }

    def matches(self, prompt: str) -> bool:
        lowered = prompt.lower()
        return any(keyword in lowered for keyword in self.keywords)

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "provider": self.provider, "keywords": self.keywords}


class ModelRouter:
    """Route prompts to the best-matching adapter by keyword, falling back to
    the first registered adapter as the default."""

    def __init__(self) -> None:
        self._adapters: list[ModelAdapter] = []

    def register(self, adapter: ModelAdapter) -> None:
        self._adapters.append(adapter)

    def route(self, prompt: str) -> dict[str, Any]:
        """Pick a single primary adapter by keyword match.

        Panel-only members (e.g. the rules engine, which weighs in on every
        panel) are never chosen as the sole primary route — they anchor
        consensus, they don't answer alone.
        """
        if not self._adapters:
            raise ValueError("No adapters registered")
        primary = [a for a in self._adapters if not getattr(a, "panel_only", False)]
        for adapter in primary:
            if adapter.matches(prompt):
                return adapter.generate(prompt)
        fallback = primary or self._adapters
        return fallback[0].generate(prompt)

    def route_all(self, prompt: str, panel: int | None = None) -> dict[str, Any]:
        """Run every matching adapter and surface disagreement as the output.

        When multiple adapters match a prompt, all of them run; dissent is
        reported whenever their results differ, instead of silently picking
        a winner. With `panel`, non-matching adapters fill the bench until
        the panel size (or the adapter count) is reached.
        """
        if not self._adapters:
            raise ValueError("No adapters registered")
        matched = [adapter for adapter in self._adapters if adapter.matches(prompt)]
        if not matched:
            matched = [self._adapters[0]]
        if panel is not None:
            for adapter in self._adapters:
                if len(matched) >= panel:
                    break
                if adapter not in matched:
                    matched.append(adapter)
        results = [adapter.generate(prompt) for adapter in matched]
        verdicts = [result.get("verdict", "abstain") for result in results]
        distribution = Counter(verdicts)
        majority = distribution.most_common(1)[0][0] if distribution else None
        return {
            "adapters": [adapter.name for adapter in matched],
            "results": results,
            "verdicts": verdicts,
            "distribution": dict(distribution),
            "majority": majority,
            "dissent": len(set(verdicts)) > 1,
        }

    def list_adapters(self) -> list[dict[str, Any]]:
        return [adapter.describe() for adapter in self._adapters]
