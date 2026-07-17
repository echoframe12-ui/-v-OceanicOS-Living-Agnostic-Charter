from __future__ import annotations

from typing import Any


class ModelAdapter:
    def __init__(self, name: str, provider: str, keywords: list[str] | None = None) -> None:
        self.name = name
        self.provider = provider
        self.keywords = [keyword.lower() for keyword in (keywords or [])]

    def generate(self, prompt: str) -> dict[str, Any]:
        return {"adapter": self.name, "provider": self.provider, "prompt": prompt}

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
        if not self._adapters:
            raise ValueError("No adapters registered")
        for adapter in self._adapters:
            if adapter.matches(prompt):
                return adapter.generate(prompt)
        return self._adapters[0].generate(prompt)

    def list_adapters(self) -> list[dict[str, Any]]:
        return [adapter.describe() for adapter in self._adapters]
