"""Readiness checks — is the service actually able to serve, not just alive?

`/health` is liveness: the process is up. Readiness is different and is what a
container orchestrator gates traffic on: are the dependencies this service needs
to do real work actually reachable right now? Here that means the SQLite database
answers and the workspace is writable. A live process with an unwritable workspace
or an unreachable database should be kept out of the load balancer until it
recovers — which is exactly what a readiness probe is for.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


def check_db(db_path: str | Path) -> bool:
    """The persistence layer answers a trivial query."""
    try:
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False


def check_workspace(workspace: str | Path) -> bool:
    """The artifact workspace exists (creatable) and is writable."""
    path = Path(workspace)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return path.is_dir() and os.access(path, os.W_OK)


def probe(db_path: str | Path, workspace: str | Path) -> dict[str, Any]:
    """Run the dependency checks and report readiness.

    `ready` reflects only the operational dependencies (db, workspace) — the
    things that decide whether the service can serve a request at all. Callers
    can fold in other signals (e.g. chain integrity) as informational context
    without gating traffic on them.
    """
    checks = {"db": check_db(db_path), "workspace": check_workspace(workspace)}
    return {"ready": all(checks.values()), "checks": checks}
