"""A persistent time series of the Composite Verification Index.

The CVI is the platform's headline trust signal, but on its own it is only a
snapshot — a number with no memory. A trust index you can't watch move can't
tell you whether verification quality is improving or slipping, which is the
whole question it exists to answer. This records the CVI at the moments it can
change, and only when it actually changes, so the series is a meaningful trend
rather than a log of identical reads.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CviHistory:
    """Change-only history of CVI snapshots, per actor (`''` = platform-wide)."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cvi_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL DEFAULT '',
                    cvi REAL NOT NULL,
                    mean_confidence REAL NOT NULL,
                    held_ratio REAL NOT NULL,
                    samples INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(self, snapshot: dict[str, Any], actor: str = "") -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO cvi_snapshots (actor, cvi, mean_confidence, held_ratio, samples, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    actor,
                    snapshot["cvi"],
                    snapshot["mean_confidence"],
                    snapshot["held_ratio"],
                    snapshot["samples"],
                    created_at,
                ),
            )
        return {"id": cursor.lastrowid, "actor": actor, "created_at": created_at, **{
            k: snapshot[k] for k in ("cvi", "mean_confidence", "held_ratio", "samples")
        }}

    def record_if_changed(
        self, snapshot: dict[str, Any], actor: str = ""
    ) -> dict[str, Any] | None:
        """Record only when the CVI or sample count differs from the latest point.

        Keeps the series a trend of real movement — reading the CVI a hundred
        times without a build in between adds no rows — and bounds growth to the
        number of times verification quality actually changed.
        """
        series = self.list(actor=actor, limit=1)
        if series:
            last = series[-1]
            if last["cvi"] == snapshot["cvi"] and last["samples"] == snapshot["samples"]:
                return None
        return self.record(snapshot, actor=actor)

    def list(self, actor: str = "", limit: int | None = None) -> list[dict[str, Any]]:
        query = (
            "SELECT id, actor, cvi, mean_confidence, held_ratio, samples, created_at "
            "FROM cvi_snapshots WHERE actor = ? ORDER BY id DESC"
        )
        params: list[Any] = [actor]
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        # fetched newest-first for the LIMIT; return oldest-first for a time series
        return [
            {
                "id": row[0],
                "actor": row[1],
                "cvi": row[2],
                "mean_confidence": row[3],
                "held_ratio": row[4],
                "samples": row[5],
                "created_at": row[6],
            }
            for row in reversed(rows)
        ]
