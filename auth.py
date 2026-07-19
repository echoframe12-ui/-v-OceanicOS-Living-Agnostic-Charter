from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from quotas import DEFAULT_TIER, is_tier

ANONYMOUS = "anonymous"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _env_admins() -> list[str]:
    return os.getenv("OCEANICOS_ADMIN_USERS", "").split(",")


class AuthRegistry:
    """SQLite-backed identity for multi-user attribution.

    Tokens are stored only as SHA-256 hashes — the raw token is returned
    once at registration and never persisted or echoed again. Dignity and
    consent: no PII is required or kept, just a chosen username.
    """

    def __init__(
        self, db_path: str | None = None, admin_users: list[str] | None = None
    ) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        source = admin_users if admin_users is not None else _env_admins()
        self.admin_users: set[str] = {name.strip() for name in source if name.strip()}
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    tier TEXT NOT NULL DEFAULT 'attestor',
                    created_at TEXT NOT NULL
                )
                """
            )

    def register(self, username: str) -> dict[str, Any]:
        cleaned = username.strip()
        if not cleaned:
            raise ValueError("A username is required to register")
        role = "admin" if cleaned in self.admin_users else "member"
        token = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO users (username, token_hash, role, tier, created_at) VALUES (?, ?, ?, ?, ?)",
                    (cleaned, _hash_token(token), role, DEFAULT_TIER, created_at),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"Username already registered: {cleaned}") from error
        return {
            "username": cleaned,
            "token": token,
            "role": role,
            "tier": DEFAULT_TIER,
            "created_at": created_at,
        }

    def set_tier(self, username: str, tier: str) -> dict[str, Any]:
        if not is_tier(tier):
            raise ValueError(f"Unknown tier: {tier}")
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE users SET tier = ? WHERE username = ?", (tier, username)
            )
        if cursor.rowcount == 0:
            raise KeyError(f"Unknown user: {username}")
        return {"username": username, "tier": tier}

    def authenticate(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT username, role, tier, created_at FROM users WHERE token_hash = ?",
                (_hash_token(token),),
            ).fetchone()
        if row is None:
            return None
        return {
            "username": row[0],
            "role": row[1],
            "tier": row[2],
            "created_at": row[3],
        }

    def list_users(self, include_role: bool = False) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT username, role, tier, created_at FROM users ORDER BY created_at"
            ).fetchall()
        result = []
        for row in rows:
            entry = {"username": row[0], "created_at": row[3]}
            if include_role:
                entry["role"] = row[1]
                entry["tier"] = row[2]
            result.append(entry)
        return result
