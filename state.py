from __future__ import annotations

from typing import Any


class StateSnapshot:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, event: str, detail: str | None = None) -> dict[str, Any]:
        entry = {"event": event, "detail": detail or ""}
        self._events.append(entry)
        return entry

    def snapshot(self) -> dict[str, Any]:
        return {"events": list(self._events), "count": len(self._events)}
