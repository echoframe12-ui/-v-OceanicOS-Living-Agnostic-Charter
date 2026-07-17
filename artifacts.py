from __future__ import annotations

from typing import Any


class ArtifactRegistry:
    def __init__(self) -> None:
        self._artifacts: list[dict[str, Any]] = []

    def create(self, name: str, kind: str, status: str = "draft") -> dict[str, Any]:
        artifact = {"name": name, "kind": kind, "status": status}
        self._artifacts.append(artifact)
        return artifact

    def list(self) -> list[dict[str, Any]]:
        return list(self._artifacts)
