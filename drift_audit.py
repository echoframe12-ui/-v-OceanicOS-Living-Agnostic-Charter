"""A persistent trail of ledger integrity audits — the Charter's "Perpetual Drift Audits."

The ledger is verifiable on demand (`verify`), but verifiable is not the same as
verified: nothing recorded that an audit ever ran, or its result over time. A
drift audit captures each integrity check — was the chain intact, was the signed
head still trustworthy, at what height, at what moment — so the record can show
not just that it *can* be checked but that it *has been*, continuously. Drift is
caught by looking, and this remembers every look.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DriftAuditLog:
    """Append-only history of `verify()` results."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS drift_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intact INTEGER NOT NULL,
                    trustworthy INTEGER NOT NULL,
                    length INTEGER NOT NULL,
                    broken_at INTEGER,
                    checked_at TEXT NOT NULL
                )
                """
            )

    def record(self, report: dict[str, Any]) -> dict[str, Any]:
        """Persist one integrity check from a `verify()` report."""
        checked_at = datetime.now(timezone.utc).isoformat()
        intact = 1 if report.get("intact") else 0
        trustworthy = 1 if report.get("trustworthy") else 0
        length = int(report.get("length", 0))
        broken_at = report.get("broken_at")
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO drift_audits (intact, trustworthy, length, broken_at, checked_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (intact, trustworthy, length, broken_at, checked_at),
            )
        return {
            "id": cursor.lastrowid,
            "intact": bool(intact),
            "trustworthy": bool(trustworthy),
            "length": length,
            "broken_at": broken_at,
            "checked_at": checked_at,
        }

    def list(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Audit history, newest first, optionally capped."""
        query = "SELECT id, intact, trustworthy, length, broken_at, checked_at FROM drift_audits ORDER BY id DESC"
        params: list[Any] = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "id": row[0],
                "intact": bool(row[1]),
                "trustworthy": bool(row[2]),
                "length": row[3],
                "broken_at": row[4],
                "checked_at": row[5],
            }
            for row in rows
        ]

    def latest(self) -> dict[str, Any] | None:
        recent = self.list(limit=1)
        return recent[0] if recent else None
