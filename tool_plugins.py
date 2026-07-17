from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server import OceanicOSService

MAX_READ_BYTES = 64 * 1024


class WorkspaceTools:
    """File tools sandboxed to a workspace directory.

    Every path is resolved and checked against the workspace root, so tool
    payloads cannot read or write outside it.
    """

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(
            root or os.getenv("OCEANICOS_WORKSPACE", "workspace")
        ).resolve()

    def _resolve(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if path != self.root and not path.is_relative_to(self.root):
            raise ValueError(f"Path escapes the workspace: {relative}")
        return path

    def list_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        pattern = payload.get("pattern", "**/*")
        if not self.root.exists():
            return {"files": [], "count": 0}
        files = sorted(
            str(path.relative_to(self.root))
            for path in self.root.glob(pattern)
            if path.is_file()
        )
        return {"files": files, "count": len(files)}

    def read_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        relative = payload.get("path", "")
        path = self._resolve(relative)
        if not path.is_file():
            raise KeyError(f"Unknown file: {relative}")
        content = path.read_text(errors="replace")[:MAX_READ_BYTES]
        return {"path": relative, "content": content}

    def write_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        relative = payload.get("path", "")
        content = str(payload.get("content", ""))
        path = self._resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"written": True, "path": relative, "bytes": len(content.encode())}


class CalendarTools:
    """Calendar events persisted to the OceanicOS SQLite database."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = payload.get("title", "")
        scheduled_for = payload.get("when", "")
        if not title or not scheduled_for:
            raise ValueError("Calendar events need both 'title' and 'when'")
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO calendar_events (title, scheduled_for, created_at) VALUES (?, ?, ?)",
                (title, scheduled_for, created_at),
            )
        return {
            "id": cursor.lastrowid,
            "title": title,
            "scheduled_for": scheduled_for,
            "created_at": created_at,
        }

    def list_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, title, scheduled_for, created_at FROM calendar_events ORDER BY scheduled_for"
            ).fetchall()
        events = [
            {"id": row[0], "title": row[1], "scheduled_for": row[2], "created_at": row[3]}
            for row in rows
        ]
        return {"events": events, "count": len(events)}


def install_tool_plugins(
    service: OceanicOSService, workspace_root: str | None = None
) -> dict[str, Any]:
    """Register the workspace and calendar tool plugins on a service."""
    workspace = WorkspaceTools(workspace_root)
    calendar = CalendarTools(str(service.db_path))
    service.register_tool("file_list", workspace.list_files)
    service.register_tool("file_read", workspace.read_file)
    service.register_tool("file_write", workspace.write_file)
    service.register_tool("calendar_add", calendar.add_event)
    service.register_tool("calendar_list", calendar.list_events)
    return {"workspace": workspace, "calendar": calendar}
