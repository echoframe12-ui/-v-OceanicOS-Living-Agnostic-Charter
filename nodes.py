from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Applied uniformly to every mounted node: the charter is agnostic, so no
# node carries locale-specific attributes — high flux, stripped identity.
STRIPPED_ATTRIBUTES = ["terrain", "currency", "affiliation"]


class NodeRegistry:
    """Mountable high-flux nodes, stripped to charter-agnostic form."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}

    def mount(self, name: str, flux: str = "high") -> dict[str, Any]:
        cleaned = name.strip().strip("/").lower()
        if not cleaned:
            raise ValueError("A node needs a name to mount")
        node = {
            "name": cleaned,
            "mount": f"/{cleaned}",
            "flux": flux,
            "agnostic": True,
            "stripped": list(STRIPPED_ATTRIBUTES),
            "mounted_at": datetime.now(timezone.utc).isoformat(),
        }
        self._nodes[cleaned] = node
        return node

    def list(self) -> list[dict[str, Any]]:
        return list(self._nodes.values())
