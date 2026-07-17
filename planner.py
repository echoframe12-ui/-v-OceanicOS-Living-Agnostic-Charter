from __future__ import annotations

from typing import Any


class Planner:
    def __init__(self) -> None:
        self._trace: list[dict[str, Any]] = []

    def plan(self, task: str, context: str | None = None) -> dict[str, Any]:
        steps = [
            {"name": "understand", "description": f"Understand the request: {task}"},
            {"name": "collect_context", "description": f"Gather context: {context or 'general context'}"},
            {"name": "execute", "description": "Perform the planned action"},
            {"name": "record", "description": "Store the outcome and lessons"},
        ]
        self._trace.append({"task": task, "steps": steps})
        return {"task": task, "steps": steps, "trace_length": len(self._trace)}

    def get_trace(self) -> list[dict[str, Any]]:
        return self._trace
