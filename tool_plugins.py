from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server import OceanicOSService

MAX_READ_BYTES = 64 * 1024
GITHUB_API = "https://api.github.com"


class WorkspaceTools:
    """File tools sandboxed to a workspace directory.

    Every path is resolved and checked against the workspace root, so tool
    payloads cannot read or write outside it.
    """

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(
            root or os.getenv("OCEANICOS_WORKSPACE", "workspace")
        ).resolve()

    def _resolve(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if path != self.root and not path.is_relative_to(self.root):
            raise ValueError(f"Path escapes the workspace: {relative}")
        return path

    def list_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        pattern = payload.get("pattern", "**/*")
        if not self.root.exists():
            return {"files": [], "count": 0}
        files = sorted(
            str(path.relative_to(self.root))
            for path in self.root.glob(pattern)
            if path.is_file()
        )
        return {"files": files, "count": len(files)}

    def read_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        relative = payload.get("path", "")
        path = self._resolve(relative)
        if not path.is_file():
            raise KeyError(f"Unknown file: {relative}")
        content = path.read_text(errors="replace")[:MAX_READ_BYTES]
        return {"path": relative, "content": content}

    def write_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        relative = payload.get("path", "")
        content = str(payload.get("content", ""))
        path = self._resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"written": True, "path": relative, "bytes": len(content.encode())}


class CalendarTools:
    """Calendar events persisted to the OceanicOS SQLite database."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = payload.get("title", "")
        scheduled_for = payload.get("when", "")
        if not title or not scheduled_for:
            raise ValueError("Calendar events need both 'title' and 'when'")
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO calendar_events (title, scheduled_for, created_at) VALUES (?, ?, ?)",
                (title, scheduled_for, created_at),
            )
        return {
            "id": cursor.lastrowid,
            "title": title,
            "scheduled_for": scheduled_for,
            "created_at": created_at,
        }

    def list_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, title, scheduled_for, created_at FROM calendar_events ORDER BY scheduled_for"
            ).fetchall()
        events = [
            {"id": row[0], "title": row[1], "scheduled_for": row[2], "created_at": row[3]}
            for row in rows
        ]
        return {"events": events, "count": len(events)}


class GitHubTools:
    """Read-only GitHub API tools with an internal ground-truth cache.

    Successful responses are cached in SQLite; when the network is
    unavailable the tools fall back to the cached copy (marked stale)
    instead of failing — the cloud is a convenience, not a covenant.
    Sends a bearer token when GITHUB_TOKEN is set.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ground_truth (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
                """
            )

    def _cache_put(self, key: str, payload: dict[str, Any]) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ground_truth (key, payload, fetched_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
            )

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT payload, fetched_at FROM ground_truth WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[0])
        payload["source"] = "ground_truth_cache"
        payload["stale"] = True
        payload["fetched_at"] = row[1]
        return payload

    def _fetch(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "oceanicos-charter",
            },
        )
        token = os.getenv("GITHUB_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())

    def _fetch_with_ground_truth(
        self, key: str, url: str, shape: Any
    ) -> dict[str, Any]:
        try:
            payload = shape(self._fetch(url))
        except (urllib.error.URLError, OSError, ValueError) as error:
            cached = self._cache_get(key)
            if cached is not None:
                return cached
            return {"error": "connection_error", "detail": str(error), "key": key}
        payload["source"] = "github_api"
        self._cache_put(key, dict(payload))
        return payload

    @staticmethod
    def _require_repo(payload: dict[str, Any]) -> tuple[str, str]:
        owner = payload.get("owner", "")
        repo = payload.get("repo", "")
        if not owner or not repo:
            raise ValueError("GitHub tools need both 'owner' and 'repo'")
        return owner, repo

    def repo_info(self, payload: dict[str, Any]) -> dict[str, Any]:
        owner, repo = self._require_repo(payload)
        url = f"{GITHUB_API}/repos/{owner}/{repo}"

        def shape(data: Any) -> dict[str, Any]:
            return {
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "default_branch": data.get("default_branch"),
                "open_issues": data.get("open_issues_count"),
            }

        return self._fetch_with_ground_truth(f"repo:{owner}/{repo}", url, shape)

    def list_issues(self, payload: dict[str, Any]) -> dict[str, Any]:
        owner, repo = self._require_repo(payload)
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues?state=open&per_page=10"

        def shape(data: Any) -> dict[str, Any]:
            issues = [
                {"number": item["number"], "title": item["title"], "state": item["state"]}
                for item in data
                if "pull_request" not in item
            ]
            return {"issues": issues, "count": len(issues)}

        return self._fetch_with_ground_truth(f"issues:{owner}/{repo}", url, shape)


def install_tool_plugins(
    service: OceanicOSService, workspace_root: str | None = None
) -> dict[str, Any]:
    """Register the workspace, calendar, and GitHub tool plugins on a service."""
    workspace = WorkspaceTools(workspace_root)
    calendar = CalendarTools(str(service.db_path))
    github = GitHubTools(str(service.db_path))
    service.register_tool("file_list", workspace.list_files)
    service.register_tool("file_read", workspace.read_file)
    service.register_tool("file_write", workspace.write_file)
    service.register_tool("calendar_add", calendar.add_event)
    service.register_tool("calendar_list", calendar.list_events)
    service.register_tool("github_repo_info", github.repo_info)
    service.register_tool("github_issues", github.list_issues)
    return {"workspace": workspace, "calendar": calendar, "github": github}
