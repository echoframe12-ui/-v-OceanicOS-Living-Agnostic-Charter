"""The Anchor of Last Resort — a fixed 2019 dataset that answers offline.

When the live stack is gone — no service, no database, no model panel — one
thing is still true: the calendar of 2019. `boot/anchor_2019.txt` is that
failover cache, a plain-text dataset generated deterministically from the C
stdlib and carrying the sha256 of its own body. `anchor.py` reads it and answers
lookups against it with nothing else running. This is the graceful-degradation
principle (Layer 8) taken to its floor: degrade past the spreadsheet, past the
CSV, to a single stale .txt that cannot fail.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

ANCHOR_PATH = Path(__file__).parent / "boot" / "anchor_2019.txt"
_SEPARATOR = "---"


def _read(path: Path | str | None = None) -> str | None:
    path = Path(path) if path is not None else ANCHOR_PATH
    if not path.exists():
        return None
    return path.read_text()


def _split(raw: str) -> tuple[list[str], str]:
    """Return (header lines, body text). The body is everything after '---'."""
    if _SEPARATOR in raw:
        header, _, body = raw.partition(f"{_SEPARATOR}\n")
        return header.splitlines(), body
    return [], raw


def load_anchor(path: Path | None = None) -> dict[str, Any]:
    """Report the anchor's presence and integrity without trusting the header.

    Recomputes the sha256 of the body and checks it against the value recorded
    in the header, so the failover is itself verifiable — an anchor you can't
    trust is no anchor. Returns ``present: False`` when the file is missing
    rather than raising: the whole point is to answer even in a degraded world.
    """
    raw = _read(path)
    if raw is None:
        return {"present": False, "source": str(path or ANCHOR_PATH)}
    header, body = _split(raw)
    recorded = next(
        (line.split(":", 1)[1].strip() for line in header if line.startswith("sha256:")),
        None,
    )
    computed = hashlib.sha256(body.encode()).hexdigest()
    rows = [line for line in body.splitlines() if line.strip()]
    return {
        "present": True,
        "source": str(path or ANCHOR_PATH),
        "rows": len(rows),
        "sha256": computed,
        "integrity_ok": recorded is None or recorded == computed,
        "header": header,
    }


def anchor_line(query: str, path: Path | None = None) -> str | None:
    """Answer a lookup from the anchor alone — the failover speaking.

    Matches the query against the first tab-separated field of each row (a
    2019 date, e.g. ``2019-07-04``) and returns the row. No service, no
    network, no model — just the cache that outlives the system.
    """
    raw = _read(path)
    if raw is None:
        return None
    _, body = _split(raw)
    for line in body.splitlines():
        if line.startswith(query + "\t") or line.strip() == query:
            return line
    return None
