"""Request tracing and structured access logging.

The third leg of observability, beside metrics and health/readiness: every
request gets a trace id (accepted from the caller for propagation, or minted)
and a structured log line, so a client report can be correlated with exactly
what the server did. The pure helpers here — id sanitizing and record building —
are kept out of the Flask hooks so they can be tested in isolation, and so the
one place that trusts a caller-supplied header is small and auditable.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

_ID_ALLOWED = re.compile(r"[^A-Za-z0-9._-]")
_MAX_ID_LEN = 64


def clean_request_id(raw: str | None) -> str:
    """Sanitize a caller-supplied trace id, or mint one.

    An inbound `X-Request-ID` is convenient for tracing across services, but it
    is attacker-controlled and flows into logs — so it is stripped to a safe
    character set and length before use. Anything that sanitizes to empty (or a
    missing header) gets a fresh minted id instead. This closes log injection
    (newlines, control chars) by construction.
    """
    if raw:
        cleaned = _ID_ALLOWED.sub("", raw)[:_MAX_ID_LEN]
        if cleaned:
            return cleaned
    return uuid.uuid4().hex[:16]


def access_record(
    request_id: str,
    method: str,
    path: str,
    status: int,
    actor: str | None,
    latency_ms: float,
) -> dict[str, Any]:
    """One structured access-log entry."""
    return {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "actor": actor,
        "latency_ms": latency_ms,
    }
