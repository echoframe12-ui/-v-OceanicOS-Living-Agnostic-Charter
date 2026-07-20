"""An append-only log of steward decisions on held attestations.

Attestations below the confidence threshold are *held*, not passed. Someone
accountable has to be able to look at a held item and decide — release it, or
uphold the hold — and that decision has to be on the record. But the held
attestation itself is part of the hash chain and must never be edited (that
would break the ledger). So a review is a *separate* record that references the
held item and carries the reviewer, verdict, and reason. The chain stays intact;
the resolution lives beside it.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RELEASE = "release"
UPHOLD = "uphold"
VERDICTS = (RELEASE, UPHOLD)


class HeldReviewLog:
    """Persistent, append-only reviews of held attestations."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS held_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attestation_id INTEGER NOT NULL,
                    reviewer TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(
        self, attestation_id: int, reviewer: str, verdict: str, reason: str
    ) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO held_reviews (attestation_id, reviewer, verdict, reason, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (attestation_id, reviewer, verdict, reason, created_at),
            )
        return {
            "id": cursor.lastrowid,
            "attestation_id": attestation_id,
            "reviewer": reviewer,
            "verdict": verdict,
            "reason": reason,
            "created_at": created_at,
        }

    def list(self, attestation_id: int | None = None) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            if attestation_id is None:
                rows = conn.execute(
                    "SELECT id, attestation_id, reviewer, verdict, reason, created_at "
                    "FROM held_reviews ORDER BY id"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, attestation_id, reviewer, verdict, reason, created_at "
                    "FROM held_reviews WHERE attestation_id = ? ORDER BY id",
                    (attestation_id,),
                ).fetchall()
        return [
            {
                "id": row[0],
                "attestation_id": row[1],
                "reviewer": row[2],
                "verdict": row[3],
                "reason": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def latest_for(self, attestation_id: int) -> dict[str, Any] | None:
        trail = self.list(attestation_id)
        return trail[-1] if trail else None

    def released_ids(self) -> set[int]:
        """Attestation ids whose latest review released them.

        Latest verdict wins: a release followed by an uphold re-holds the item,
        and an uphold followed by a release frees it. Only the current decision
        counts, so the record can change its mind without losing the history.
        """
        latest: dict[int, str] = {}
        for review in self.list():
            latest[review["attestation_id"]] = review["verdict"]
        return {att_id for att_id, verdict in latest.items() if verdict == RELEASE}
