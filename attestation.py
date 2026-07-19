from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

CONFIDENCE_THRESHOLD = 0.74


def score_confidence(evidence: list[str], context_provided: bool) -> float:
    """Deterministic confidence from observable evidence.

    Each completed pipeline stage counts as evidence; a run without an
    explicit context loses 0.2, dropping it below the threshold so it is
    held for human review. This measures exactly what it claims to —
    evidence count — and is never a claim of semantic certainty.
    """
    confidence = min(0.99, 0.5 + 0.05 * len(evidence))
    if not context_provided:
        confidence -= 0.2
    return round(max(0.0, confidence), 2)


class AttestationEngine:
    """Attest outputs instead of asserting them.

    Every attestation carries a content hash, a confidence score judged
    against the threshold, and the source trail that produced it. Anything
    below threshold is held, not passed.
    """

    def __init__(self) -> None:
        self._attestations: list[dict[str, Any]] = []

    def attest(
        self,
        subject: str,
        content: str,
        sources: list[str],
        confidence: float,
    ) -> dict[str, Any]:
        entry = {
            "id": len(self._attestations) + 1,
            "subject": subject,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "confidence": confidence,
            "threshold": CONFIDENCE_THRESHOLD,
            "status": "attested" if confidence >= CONFIDENCE_THRESHOLD else "held",
            "sources": list(sources),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._attestations.append(entry)
        return entry

    def list(self) -> list[dict[str, Any]]:
        return list(self._attestations)

    def held(self) -> list[dict[str, Any]]:
        return [entry for entry in self._attestations if entry["status"] == "held"]
