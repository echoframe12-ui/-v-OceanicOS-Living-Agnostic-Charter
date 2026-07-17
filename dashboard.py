from __future__ import annotations

from typing import Any


class Dashboard:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, title: str, kind: str, status: str = "active") -> dict[str, Any]:
        item = {"title": title, "kind": kind, "status": status}
        self._items.append(item)
        return item

    def summary(self) -> dict[str, Any]:
        return {
            "count": len(self._items),
            "items": list(self._items),
        }
