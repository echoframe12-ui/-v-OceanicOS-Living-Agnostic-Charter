from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class OceanicOSService:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        self._memory: list[dict[str, Any]] = []
        self._tools = {
            "echo": self._echo_tool,
            "timestamp": self._timestamp_tool,
            "word_count": self._word_count_tool,
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    context TEXT NOT NULL,
                    artifact TEXT NOT NULL,
                    stages TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @property
    def db_path(self) -> Path:
        return self._db_path

    def register_tool(self, name: str, handler: Any) -> dict[str, Any]:
        self._tools[name] = handler
        return {"registered": True, "name": name}

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "OceanicOS",
            "charter": "Ω∞v OceanicOS Living Agnostic Charter",
        }

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

    def record_build(
        self,
        task: str,
        context: str,
        artifact: str,
        stages: list[str],
    ) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO builds (task, context, artifact, stages, created_at) VALUES (?, ?, ?, ?, ?)",
                (task, context, artifact, json.dumps(stages), created_at),
            )
        return {
            "id": cursor.lastrowid,
            "task": task,
            "context": context,
            "artifact": artifact,
            "stages": stages,
            "created_at": created_at,
        }

    def list_builds(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, task, context, artifact, stages, created_at FROM builds ORDER BY id"
            ).fetchall()
        return [
            {
                "id": row[0],
                "task": row[1],
                "context": row[2],
                "artifact": row[3],
                "stages": json.loads(row[4]),
                "created_at": row[5],
            }
            for row in rows
        ]

    def _echo_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": payload.get("message", "")}

    def _timestamp_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": datetime.now(timezone.utc).isoformat()}

    def _word_count_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": len(str(payload.get("text", "")).split())}
