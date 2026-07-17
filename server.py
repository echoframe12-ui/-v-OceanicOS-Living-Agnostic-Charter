from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class OceanicOSService:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or "oceanicos.db")
        self._memory: list[dict[str, Any]] = []
        self._tools = {
            "echo": self._echo_tool,
        }
        self._plugins: list[dict[str, Any]] = []
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plugins (
                    name TEXT PRIMARY KEY,
                    config TEXT NOT NULL
                )
                """
            )

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "service": "OceanicOS"}

    def create_plan(self, task: str) -> dict[str, Any]:
        return {
            "task": task,
            "steps": [
                "Clarify the goal",
                "Gather relevant context",
                "Execute the work",
                "Record the outcome",
            ],
        }

    def store_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(entry)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("INSERT INTO memory (payload) VALUES (?)", (payload,))
        self._memory.append(entry)
        return {"stored": True, "count": len(self._memory)}

    def search_memory(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT payload FROM memory").fetchall()
        entries = [json.loads(row[0]) for row in rows]
        self._memory = entries
        return [entry for entry in entries if q in str(entry.get("text", "")).lower()]

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": name} for name in sorted(self._tools)]

    def invoke_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](payload)

    def register_plugin(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plugins (name, config) VALUES (?, ?)",
                (name, json.dumps(config)),
            )
        self._plugins.append({"name": name, "config": config})
        return {"registered": True, "name": name}

    def list_plugins(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT name, config FROM plugins").fetchall()
        self._plugins = [{"name": row[0], "config": json.loads(row[1])} for row in rows]
        return self._plugins

    def _echo_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": payload.get("message", "")}
