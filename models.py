from __future__ import annotations

from typing import Any


class ModelAdapter:
    def __init__(self, name: str, provider: str) -> None:
        self.name = name
        self.provider = provider

    def generate(self, prompt: str) -> dict[str, Any]:
        return {"adapter": self.name, "provider": self.provider, "prompt": prompt}


class ModelRouter:
    def __init__(self) -> None:
        self._adapters: list[ModelAdapter] = []

    def register(self, adapter: ModelAdapter) -> None:
        self._adapters.append(adapter)

    def route(self, prompt: str) -> dict[str, Any]:
        if not self._adapters:
            raise ValueError("No adapters registered")
        adapter = self._adapters[0]
        return adapter.generate(prompt)
