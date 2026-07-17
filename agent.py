from __future__ import annotations

from typing import Any


class AgentLoop:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def run(self, task: str, context: str | None = None) -> dict[str, Any]:
        self._events.append({"event": "start", "task": task})
        self._events.append({"event": "plan", "context": context or "general"})
        self._events.append({"event": "finish", "task": task})
        return {"task": task, "events": self._events}

    def events(self) -> list[dict[str, Any]]:
        return self._events
