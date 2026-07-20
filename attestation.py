from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIDENCE_THRESHOLD = 0.74


def consensus_delta(verdicts: list[str]) -> float:
    """Confidence adjustment from a dissent panel's verdicts.

    Unanimous approval raises confidence; unanimous "revise" lowers it enough
    to hold even a well-evidenced build; a split nudges by its majority.
    Abstentions (adapters without a verdict) count for nothing — the panel
    only moves the score when it actually has an opinion.
    """
    approve = verdicts.count("approve")
    revise = verdicts.count("revise")
    if approve == 0 and revise == 0:
        return 0.0
    if approve == len(verdicts):
        return 0.1
    if revise == len(verdicts):
        return -0.2
    if approve > revise:
        return 0.05
    if revise > approve:
        return -0.1
    return 0.0


def score_confidence(
    evidence: list[str], context_provided: bool, consensus: float = 0.0
) -> float:
    """Deterministic confidence from observable evidence and panel consensus.

    Each completed pipeline stage counts as evidence; a run without an
    explicit context loses 0.2. The `consensus` delta (from a dissent panel's
    verdicts) can then push a borderline build across the hold threshold in
    either direction — surfacing disagreement into the decision, not beside
    it. This measures exactly what it claims to and is never a claim of
    semantic certainty.
    """
    confidence = 0.5 + 0.05 * len(evidence)
    if not context_provided:
        confidence -= 0.2
    confidence += consensus
    return round(max(0.0, min(0.99, confidence)), 2)


class AttestationEngine:
    """Attest outputs instead of asserting them.

    Every attestation carries a content hash, a confidence score judged
    against the threshold, and the source trail that produced it. Anything
    below threshold is held, not passed.

    Attestations are persisted in the OceanicOS SQLite database, so the record
    — and the CVI computed from it — is shared across gunicorn workers and
    survives restarts. Without this, each worker held its own in-memory record
    and reported a different CVI; the ground truth of what was verified now
    lives in one place.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attestations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    actor TEXT NOT NULL DEFAULT 'anonymous',
                    sha256 TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    threshold REAL NOT NULL,
                    status TEXT NOT NULL,
                    sources TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
                """
            )

    def attest(
        self,
        subject: str,
        content: str,
        sources: list[str],
        confidence: float,
        actor: str = "anonymous",
    ) -> dict[str, Any]:
        status = "attested" if confidence >= CONFIDENCE_THRESHOLD else "held"
        created_at = datetime.now(timezone.utc).isoformat()
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO attestations
                    (subject, actor, sha256, confidence, threshold, status, sources, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subject,
                    actor,
                    sha256,
                    confidence,
                    CONFIDENCE_THRESHOLD,
                    status,
                    json.dumps(list(sources)),
                    created_at,
                ),
            )
        return {
            "id": cursor.lastrowid,
            "subject": subject,
            "actor": actor,
            "sha256": sha256,
            "confidence": confidence,
            "threshold": CONFIDENCE_THRESHOLD,
            "status": status,
            "sources": list(sources),
            "created_at": created_at,
        }

    def _rows(self, where: str = "", params: tuple = ()) -> list[dict[str, Any]]:
        query = (
            "SELECT id, subject, actor, sha256, confidence, threshold, status, "
            "sources, created_at FROM attestations "
        ) + where + " ORDER BY id"
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": row[0],
                "subject": row[1],
                "actor": row[2],
                "sha256": row[3],
                "confidence": row[4],
                "threshold": row[5],
                "status": row[6],
                "sources": json.loads(row[7]),
                "created_at": row[8],
            }
            for row in rows
        ]

    def list(self, actor: str | None = None) -> list[dict[str, Any]]:
        if actor is None:
            return self._rows()
        return self._rows("WHERE actor = ?", (actor,))

    def held(self) -> list[dict[str, Any]]:
        return self._rows("WHERE status = ?", ("held",))

    def cvi(self, actor: str | None = None) -> dict[str, Any]:
        """Composite Verification Index — evidence-weighted trust, 0.0 to 1.0.

        Mean attestation confidence discounted by the held ratio. Scoped to an
        actor when given. An empty record scores 0.0: no evidence, no trust.
        """
        scope = self.list(actor)
        total = len(scope)
        if total == 0:
            return {"cvi": 0.0, "samples": 0, "mean_confidence": 0.0, "held_ratio": 0.0}
        mean_confidence = sum(a["confidence"] for a in scope) / total
        held_ratio = len([a for a in scope if a["status"] == "held"]) / total
        return {
            "cvi": round(mean_confidence * (1 - held_ratio), 3),
            "samples": total,
            "mean_confidence": round(mean_confidence, 3),
            "held_ratio": round(held_ratio, 3),
        }
