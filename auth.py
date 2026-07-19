from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ANONYMOUS = "anonymous"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthRegistry:
    """SQLite-backed identity for multi-user attribution.

    Tokens are stored only as SHA-256 hashes — the raw token is returned
    once at registration and never persisted or echoed again. Dignity and
    consent: no PII is required or kept, just a chosen username.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def register(self, username: str) -> dict[str, Any]:
        cleaned = username.strip()
        if not cleaned:
            raise ValueError("A username is required to register")
        token = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO users (username, token_hash, created_at) VALUES (?, ?, ?)",
                    (cleaned, _hash_token(token), created_at),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"Username already registered: {cleaned}") from error
        return {"username": cleaned, "token": token, "created_at": created_at}

    def authenticate(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT username, created_at FROM users WHERE token_hash = ?",
                (_hash_token(token),),
            ).fetchone()
        if row is None:
            return None
        return {"username": row[0], "created_at": row[1]}

    def list_users(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT username, created_at FROM users ORDER BY created_at"
            ).fetchall()
        return [{"username": row[0], "created_at": row[1]} for row in rows]
