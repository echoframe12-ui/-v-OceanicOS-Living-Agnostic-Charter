"""A persistent ledger of dissent — the panel's disagreement, kept as data.

The Doctrine's axiom is *dissent is data*: disagreement between models is the
primary signal, not noise. Yet the consensus panel computed its verdicts and
discarded them the moment the response was sent. This records every panel
evaluation — how split it was, what the majority was, when — so dissent becomes a
queryable trend instead of a fact that evaporates.

Only the *hash* of the prompt is stored, never its text, so the ledger is a safe
aggregate: it remembers that the panel disagreed and how much, not what about.
Same separate-table discipline as the drift-audit and CVI-history logs.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def dissent_score(verdicts: list[str]) -> float:
    """How split the panel was, 0.0 (unanimous) to near 1.0 (evenly divided).

    The fraction of *opinionated* verdicts (approve/revise, abstentions excluded)
    that fall outside the plurality. Unanimous opinion scores 0.0; a 2–2 split
    scores 0.5; all-abstain scores 0.0 (no opinion, no dissent).
    """
    opinions = [v for v in verdicts if v in ("approve", "revise")]
    if not opinions:
        return 0.0
    plurality = Counter(opinions).most_common(1)[0][1]
    return round(1 - plurality / len(opinions), 3)


class ConsensusLog:
    """Append-only history of dissent-panel evaluations."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consensus_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_sha256 TEXT NOT NULL,
                    adapters INTEGER NOT NULL,
                    majority TEXT,
                    dissent INTEGER NOT NULL,
                    dissent_score REAL NOT NULL,
                    verdicts TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(self, prompt: str, result: dict[str, Any]) -> dict[str, Any]:
        """Persist one panel evaluation from a `route_all` result (prompt hashed)."""
        verdicts = list(result.get("verdicts", []))
        score = dissent_score(verdicts)
        entry = {
            "prompt_sha256": hashlib.sha256(str(prompt).encode()).hexdigest(),
            "adapters": len(result.get("adapters", [])),
            "majority": result.get("majority"),
            "dissent": bool(result.get("dissent")),
            "dissent_score": score,
            "verdicts": verdicts,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO consensus_evaluations "
                "(prompt_sha256, adapters, majority, dissent, dissent_score, verdicts, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    entry["prompt_sha256"],
                    entry["adapters"],
                    entry["majority"],
                    1 if entry["dissent"] else 0,
                    score,
                    json.dumps(verdicts),
                    entry["created_at"],
                ),
            )
        return {"id": cursor.lastrowid, **entry}

    def list(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Evaluation history, newest first, optionally capped."""
        query = (
            "SELECT id, prompt_sha256, adapters, majority, dissent, dissent_score, verdicts, created_at "
            "FROM consensus_evaluations ORDER BY id DESC"
        )
        params: list[Any] = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "id": row[0],
                "prompt_sha256": row[1],
                "adapters": row[2],
                "majority": row[3],
                "dissent": bool(row[4]),
                "dissent_score": row[5],
                "verdicts": json.loads(row[6]),
                "created_at": row[7],
            }
            for row in rows
        ]

    def stats(self) -> dict[str, Any]:
        """Aggregate dissent — total evaluations, dissent rate, mean split."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(dissent), 0), COALESCE(AVG(dissent_score), 0.0) "
                "FROM consensus_evaluations"
            ).fetchone()
        total, dissent_count, mean_score = row[0], row[1], row[2]
        return {
            "evaluations": total,
            "dissent_count": dissent_count,
            "dissent_rate": round(dissent_count / total, 3) if total else 0.0,
            "mean_dissent_score": round(mean_score, 3),
        }
