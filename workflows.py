from __future__ import annotations

from typing import Any


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: dict[str, list[dict[str, Any]]] = {}

    def create_workflow(self, name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        self._workflows[name] = steps
        return {"created": True, "name": name, "steps": len(steps)}

    def get_workflow(self, name: str) -> dict[str, Any]:
        if name not in self._workflows:
            raise KeyError(f"Unknown workflow: {name}")
        return {"name": name, "steps": self._workflows[name]}

    def execute_workflow(self, name: str) -> dict[str, Any]:
        workflow = self.get_workflow(name)
        return {"executed": True, "name": name, "steps": workflow["steps"]}
