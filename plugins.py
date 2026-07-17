from __future__ import annotations

from typing import Any


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[dict[str, Any]] = []

    def register(self, name: str, capabilities: list[str]) -> dict[str, Any]:
        plugin = {"name": name, "capabilities": capabilities}
        self._plugins.append(plugin)
        return plugin

    def list(self) -> list[dict[str, Any]]:
        return list(self._plugins)
