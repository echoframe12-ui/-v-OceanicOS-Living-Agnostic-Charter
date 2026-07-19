from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

CONFIDENCE_THRESHOLD = 0.74


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
    """

    def __init__(self) -> None:
        self._attestations: list[dict[str, Any]] = []

    def attest(
        self,
        subject: str,
        content: str,
        sources: list[str],
        confidence: float,
        actor: str = "anonymous",
    ) -> dict[str, Any]:
        entry = {
            "id": len(self._attestations) + 1,
            "subject": subject,
            "actor": actor,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "confidence": confidence,
            "threshold": CONFIDENCE_THRESHOLD,
            "status": "attested" if confidence >= CONFIDENCE_THRESHOLD else "held",
            "sources": list(sources),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._attestations.append(entry)
        return entry

    def list(self, actor: str | None = None) -> list[dict[str, Any]]:
        if actor is None:
            return list(self._attestations)
        return [entry for entry in self._attestations if entry["actor"] == actor]

    def held(self) -> list[dict[str, Any]]:
        return [entry for entry in self._attestations if entry["status"] == "held"]

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
