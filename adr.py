"""Serve the Architecture Decision Records — the platform's own governance.

Every significant design choice is written down in `DECISIONS/` as a numbered
record: the context, the decision, and its consequences. A platform built on
accountability and provenance should not keep that log only in the repo — it
should be able to show, at runtime, why it is the way it is. This reads the ADR
files and exposes them, so the reasoning behind the system is a first-class,
inspectable part of the running system.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_ADR_DIR = Path(__file__).parent / "DECISIONS"
_FILENAME = re.compile(r"^(\d+)-(.+)\.md$")
# strip "# ", an optional "Decision " word, and a leading "NNNN <sep>" prefix
_HEADING = re.compile(r"^#\s*(?:Decision\s+)?(?:\d+\s*[—:\-]\s*)?(.*)$")


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            match = _HEADING.match(line.strip())
            return match.group(1).strip() if match and match.group(1).strip() else fallback
    return fallback


def list_adr(directory: Path | str | None = None) -> list[dict[str, Any]]:
    """Every ADR as `{number, title, filename}`, ordered by number."""
    directory = Path(directory) if directory else _ADR_DIR
    records = []
    for path in directory.glob("[0-9]*.md"):
        match = _FILENAME.match(path.name)
        if not match:
            continue
        number = int(match.group(1))
        records.append(
            {
                "number": number,
                "title": _title(path.read_text(), match.group(2).replace("-", " ")),
                "filename": path.name,
            }
        )
    return sorted(records, key=lambda r: r["number"])


def get_adr(number: int, directory: Path | str | None = None) -> dict[str, Any] | None:
    """One ADR with its full markdown, or None if there is no such number."""
    directory = Path(directory) if directory else _ADR_DIR
    for path in directory.glob("[0-9]*.md"):
        match = _FILENAME.match(path.name)
        if match and int(match.group(1)) == number:
            text = path.read_text()
            return {
                "number": number,
                "title": _title(text, match.group(2).replace("-", " ")),
                "filename": path.name,
                "content": text,
            }
    return None
