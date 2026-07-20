from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class UsageLog:
    """A persistent, per-actor audit trail of billable activity.

    Every metered event — a build, a quota block, a tier change — is recorded
    with the actor, the tier in force at the time, and a timestamp, so quotas
    become auditable history rather than a running count. Persisted in the
    OceanicOS SQLite database; survives restarts.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT '',
                    detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(
        self, actor: str, action: str, tier: str = "", detail: str = ""
    ) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO usage (actor, action, tier, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                (actor, action, tier, detail, created_at),
            )
        return {
            "id": cursor.lastrowid,
            "actor": actor,
            "action": action,
            "tier": tier,
            "detail": detail,
            "created_at": created_at,
        }

    def list(self, actor: str | None = None) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            if actor is None:
                rows = conn.execute(
                    "SELECT id, actor, action, tier, detail, created_at FROM usage ORDER BY id"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, actor, action, tier, detail, created_at FROM usage WHERE actor = ? ORDER BY id",
                    (actor,),
                ).fetchall()
        return [
            {
                "id": row[0],
                "actor": row[1],
                "action": row[2],
                "tier": row[3],
                "detail": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def summary(self, actor: str | None = None) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for event in self.list(actor):
            counts[event["action"]] = counts.get(event["action"], 0) + 1
        return {"actor": actor, "total": sum(counts.values()), "by_action": counts}

    def count_in_window(
        self,
        actor: str,
        action: str,
        window_seconds: int,
        now: datetime | None = None,
    ) -> tuple[int, str | None]:
        """Count an actor's events of one action within a rolling window.

        Returns the count and the oldest in-window timestamp (ISO 8601), which
        the caller can add to the window to compute when a slot frees. `now`
        is injectable so windowing is testable without real time passing.
        """
        now = now or datetime.now(timezone.utc)
        cutoff = (now - timedelta(seconds=window_seconds)).isoformat()
        stamps = sorted(
            event["created_at"]
            for event in self.list(actor)
            if event["action"] == action and event["created_at"] >= cutoff
        )
        return len(stamps), (stamps[0] if stamps else None)
