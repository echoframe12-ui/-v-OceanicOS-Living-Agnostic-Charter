from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIDENCE_THRESHOLD = 0.74

# The chain's genesis link: what the first attestation points back to.
GENESIS_HASH = "0" * 64

# Fields covered by an attestation's link hash. Any retroactive edit to one of
# these on a past row changes its entry_hash, which every later row's prev_hash
# depends on — so the break propagates to the tail and `verify_chain` catches it.
_LINKED_FIELDS = (
    "subject",
    "actor",
    "sha256",
    "confidence",
    "threshold",
    "status",
    "sources",
    "created_at",
)


def link_hash(prev_hash: str, entry: dict[str, Any]) -> str:
    """The tamper-evident hash for one attestation, chained to its predecessor.

    Covers the entry's content fields and the previous entry's hash, so the
    ledger is a hash chain: change any past attestation and its hash no longer
    matches, breaking the link every later entry was built on.
    """
    payload = json.dumps(
        {field: entry[field] for field in _LINKED_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256((prev_hash + payload).encode()).hexdigest()


def checkpoint_signature(key: str, head_hash: str, length: int) -> str:
    """The HMAC that seals a chain head at a given length.

    A module-level pure function so the running engine and the standalone
    offline verifier compute the signature the same way — one source of truth,
    exactly as `link_hash` is for the chain itself. The key is an operator
    secret held outside the ledger; without it, the signature cannot be forged.
    """
    return hmac.new(
        key.encode(), f"{head_hash}:{length}".encode(), hashlib.sha256
    ).hexdigest()


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

    The record is also a hash chain: each attestation carries the previous
    entry's hash and its own, so the ledger attests to itself. Any retroactive
    edit breaks the chain from that point on, and `verify_chain` finds where.
    A platform that verifies outputs has no business keeping a ledger anyone
    could silently rewrite.
    """

    _COLUMNS = (
        "id, subject, actor, sha256, confidence, threshold, status, "
        "sources, created_at, prev_hash, entry_hash"
    )

    def __init__(self, db_path: str | None = None, signing_key: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        self._signing_key = (
            signing_key if signing_key is not None else os.getenv("OCEANICOS_SIGNING_KEY", "")
        )
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
                    created_at TEXT NOT NULL,
                    prev_hash TEXT NOT NULL DEFAULT '',
                    entry_hash TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attestation_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    head_hash TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    signature TEXT NOT NULL
                )
                """
            )
            # Migrate a pre-chain table forward without losing its rows.
            existing = {row[1] for row in conn.execute("PRAGMA table_info(attestations)")}
            for column in ("prev_hash", "entry_hash"):
                if column not in existing:
                    conn.execute(
                        f"ALTER TABLE attestations ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
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
        entry = {
            "subject": subject,
            "actor": actor,
            "sha256": sha256,
            "confidence": confidence,
            "threshold": CONFIDENCE_THRESHOLD,
            "status": status,
            "sources": list(sources),
            "created_at": created_at,
        }
        # Acquire the write lock before reading the tail so two workers can't
        # link two new entries onto the same predecessor and fork the chain.
        conn = sqlite3.connect(self._db_path, isolation_level=None)
        try:
            conn.execute("BEGIN IMMEDIATE")
            tail = conn.execute(
                "SELECT entry_hash FROM attestations ORDER BY id DESC LIMIT 1"
            ).fetchone()
            prev_hash = tail[0] if tail else GENESIS_HASH
            entry_hash = link_hash(prev_hash, entry)
            cursor = conn.execute(
                """
                INSERT INTO attestations
                    (subject, actor, sha256, confidence, threshold, status,
                     sources, created_at, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    prev_hash,
                    entry_hash,
                ),
            )
            row_id = cursor.lastrowid
            conn.execute("COMMIT")
        finally:
            conn.close()
        return {
            "id": row_id,
            **entry,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
        }

    def _rows(self, where: str = "", params: tuple = ()) -> list[dict[str, Any]]:
        query = (
            f"SELECT {self._COLUMNS} FROM attestations "
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
                "prev_hash": row[9],
                "entry_hash": row[10],
            }
            for row in rows
        ]

    def verify_chain(self) -> dict[str, Any]:
        """Walk the ledger and confirm no attestation was retroactively altered.

        Recomputes each entry's link hash from its content and its recorded
        predecessor, and checks the chain is continuous. Returns whether the
        record is intact and, if not, the id of the first broken link — the
        point at or before which the ledger was tampered with.
        """
        rows = self._rows()
        prev_hash = GENESIS_HASH
        for entry in rows:
            expected = link_hash(prev_hash, entry)
            if entry["prev_hash"] != prev_hash or entry["entry_hash"] != expected:
                return {"intact": False, "length": len(rows), "broken_at": entry["id"]}
            prev_hash = entry["entry_hash"]
        return {"intact": True, "length": len(rows), "broken_at": None, "head": prev_hash}

    @property
    def can_sign(self) -> bool:
        """Whether a signing key is configured. No key, no signed checkpoints."""
        return bool(self._signing_key)

    def _sign(self, head_hash: str, length: int) -> str:
        return checkpoint_signature(self._signing_key, head_hash, length)

    def checkpoint(self) -> dict[str, Any]:
        """Seal the current chain head with a signature the key-holder alone can make.

        A checkpoint is an HMAC over the head hash and length, keyed by an
        operator secret that never touches the database. It raises the bar from
        tamper-*evident* to tamper-*resistant*: an attacker who rewrites the
        ledger and recomputes the chain forward still cannot forge a checkpoint
        that matches their new head without the key. Refuses to seal a chain
        that is already broken — a checkpoint should only ever bless the truth.
        """
        if not self._signing_key:
            raise RuntimeError("no signing key configured (set OCEANICOS_SIGNING_KEY)")
        report = self.verify_chain()
        if not report["intact"]:
            raise RuntimeError(
                f"refusing to checkpoint a broken chain (first break at {report['broken_at']})"
            )
        head = report["head"]
        length = report["length"]
        created_at = datetime.now(timezone.utc).isoformat()
        signature = self._sign(head, length)
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO attestation_checkpoints (head_hash, length, created_at, signature) "
                "VALUES (?, ?, ?, ?)",
                (head, length, created_at, signature),
            )
        return {
            "id": cursor.lastrowid,
            "head_hash": head,
            "length": length,
            "created_at": created_at,
            "signature": signature,
        }

    def latest_checkpoint(self) -> dict[str, Any] | None:
        checkpoints = self.list_checkpoints()
        return checkpoints[-1] if checkpoints else None

    def list_checkpoints(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, head_hash, length, created_at, signature "
                "FROM attestation_checkpoints ORDER BY id"
            ).fetchall()
        return [
            {
                "id": row[0],
                "head_hash": row[1],
                "length": row[2],
                "created_at": row[3],
                "signature": row[4],
            }
            for row in rows
        ]

    def verify(self) -> dict[str, Any]:
        """Full integrity report: the chain walk plus the signed checkpoint.

        `verify_chain` proves the record wasn't edited in place. The checkpoint
        proves it wasn't rewritten wholesale: even a fully-recomputed forward
        chain fails here, because its head no longer matches the signed head and
        only the key-holder can sign a new one. A record is trustworthy when the
        chain is intact, a checkpoint exists, its head is still reproduced, and
        its signature validates under the current key.
        """
        chain = self.verify_chain()
        cp = self.latest_checkpoint()
        if cp is None:
            return {**chain, "checkpointed": False}
        rows = self._rows()
        head_reproduced = (
            len(rows) >= cp["length"] > 0
            and rows[cp["length"] - 1]["entry_hash"] == cp["head_hash"]
        ) or (cp["length"] == 0 and cp["head_hash"] == GENESIS_HASH)
        signature_valid = self.can_sign and hmac.compare_digest(
            cp["signature"], self._sign(cp["head_hash"], cp["length"])
        )
        return {
            **chain,
            "checkpointed": True,
            "checkpoint": {
                "head_hash": cp["head_hash"],
                "length": cp["length"],
                "created_at": cp["created_at"],
                "signature_valid": signature_valid,
                "head_reproduced": head_reproduced,
            },
            "trustworthy": bool(
                chain["intact"] and head_reproduced and signature_valid
            ),
        }

    def export(self) -> dict[str, Any]:
        """The whole sealed record as a self-contained, portable bundle.

        Carries every attestation and every checkpoint, so the chain and its
        seals can be verified offline — by `verify_ledger.py` — with no service,
        no database, and no engine. This is the attestation ledger's answer to
        the platform's own principle that the ground truth should survive the
        system: trust in the record becomes portable, not service-bound.
        """
        return {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "genesis": GENESIS_HASH,
            "attestations": self.list(),
            "checkpoints": self.list_checkpoints(),
        }

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
