"""Supersession links — which attestation re-verifies (replaces) which, over versions.

The ledger is append-only: an attestation is never edited or deleted. But an
artifact evolves, and a later attestation may re-verify a revised version of what
an earlier one covered. Subject history (`DECISIONS/0046`) groups by name; this
records the *explicit* link — attestation N supersedes attestation M — so a
consumer can ask "is this the current verified version, or has it been
superseded?" without inferring it.

A separate append-only table, like the held-review and drift-audit logs: recording
a supersession touches neither the attestation chain nor its hashes. A supersession
is a claim *about* the record, kept beside it, not a change *to* it.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SupersessionLog:
    """Append-only record of `new_id supersedes old_id` links."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS supersessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    old_id INTEGER NOT NULL,
                    new_id INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(self, old_id: int, new_id: int, actor: str, reason: str) -> dict[str, Any]:
        """Record that `new_id` supersedes `old_id`."""
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO supersessions (old_id, new_id, actor, reason, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (int(old_id), int(new_id), actor, reason, created_at),
            )
        return {
            "id": cursor.lastrowid,
            "old_id": int(old_id),
            "new_id": int(new_id),
            "actor": actor,
            "reason": reason,
            "created_at": created_at,
        }

    def list(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, old_id, new_id, actor, reason, created_at "
                "FROM supersessions ORDER BY id"
            ).fetchall()
        return [
            {
                "id": row[0],
                "old_id": row[1],
                "new_id": row[2],
                "actor": row[3],
                "reason": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def exists(self, old_id: int, new_id: int) -> bool:
        """Whether this exact supersession link is already recorded (idempotence guard)."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM supersessions WHERE old_id = ? AND new_id = ? LIMIT 1",
                (int(old_id), int(new_id)),
            ).fetchone()
        return row is not None

    def lineage(self, att_id: int) -> dict[str, Any]:
        """The supersession lineage of one attestation.

        `supersedes`: the ids this attestation replaces. `superseded_by`: the ids
        that replace it. `is_current`: true when nothing supersedes it — the answer
        to "is this the current verified version?".
        """
        rows = self.list()
        supersedes = [r["old_id"] for r in rows if r["new_id"] == att_id]
        superseded_by = [r["new_id"] for r in rows if r["old_id"] == att_id]
        return {
            "id": att_id,
            "supersedes": supersedes,
            "superseded_by": superseded_by,
            "is_current": not superseded_by,
        }
