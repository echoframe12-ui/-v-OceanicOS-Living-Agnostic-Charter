"""A signed, portable digest of the platform's own trust posture at a moment.

The per-attestation receipt proves one record; the checkpoint signs the ledger
head. This signs the *platform's self-report*: a compact, canonical snapshot of
the posture (`/status.json` in miniature) plus an operator-key HMAC, so a third
party handed the digest can confirm it genuinely came from this platform at that
time — not a fabricated "we were healthy" claim. Attest, don't assert, even about
your own health.

Pure functions over a dict; the same signing discipline as `checkpoint_signature`
(`attestation.py`), keyed by the operator secret that never leaves the process.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

# The fields the signature covers. Presentation-only extras a caller may attach
# (e.g. `signed`) are deliberately excluded, so re-signing is unambiguous.
SIGNABLE_FIELDS = (
    "posture",
    "cvi",
    "sourced_ratio",
    "chain_intact",
    "trustworthy",
    "chain_length",
    "held_pending",
    "held_breached",
    "checkpoint_head",
    "generated_at",
)


def canonical(payload: dict[str, Any]) -> str:
    """The canonical, signature-covered form: the signable fields, sorted, compact.

    Deterministic (sorted keys, no whitespace) so the same posture always yields
    the same bytes to sign and verify, independent of dict ordering.
    """
    return json.dumps(
        {field: payload.get(field) for field in SIGNABLE_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def sign(key: str, payload: dict[str, Any]) -> str:
    """HMAC-SHA256 of the canonical posture under the operator key."""
    return hmac.new(key.encode(), canonical(payload).encode(), hashlib.sha256).hexdigest()


def verify(payload: dict[str, Any], signature: str, key: str | None) -> bool:
    """True when `signature` is a valid operator-key HMAC over `payload`.

    Requires a key (an unsigned digest is never "verified") and a constant-time
    compare, exactly as the checkpoint signature check does.
    """
    if not key or not signature:
        return False
    return hmac.compare_digest(signature, sign(key, payload))
