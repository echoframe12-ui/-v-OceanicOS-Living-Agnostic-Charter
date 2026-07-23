"""The platform's compounding footprint — what its append-only ledgers have accrued.

The Doctrine's loop ends *Recompile → Compound*: memory compounds, artifacts
compound. The platform keeps not one record but many — attestations, checkpoints,
builds, drift audits, the CVI trend, held-review decisions, dissent evaluations,
and the decision log of its own evolution — each append-only, each only ever
growing. This module reports that accrual as one legible number per ledger, so
"the histories compound" is a figure you can read rather than a claim.

Pure: `compounding` takes the counts and structures them; the endpoint gathers
them from the live singletons.
"""
from __future__ import annotations

from typing import Any

# Human-facing descriptions of what each ledger accrues.
LEDGER_NOTES = {
    "attestations": "verification records, hash-chained",
    "checkpoints": "signed seals of the chain head",
    "builds": "build ledger entries",
    "drift_audits": "recorded integrity checks",
    "cvi_history": "trust-index trend points",
    "held_reviews": "steward decisions on held items",
    "consensus_evaluations": "dissent-panel evaluations",
    "decisions": "architecture decision records (rounds of evolution)",
}


def compounding(ledgers: dict[str, int]) -> dict[str, Any]:
    """Structure the per-ledger counts into a compounding footprint.

    `records_total` is the sum across every append-only ledger — the platform's
    whole accrued memory — and `ledgers` carries each count with a note. The
    record only grows: nothing here is ever rewritten, only appended.
    """
    described = {
        name: {"count": count, "accrues": LEDGER_NOTES.get(name, "")}
        for name, count in ledgers.items()
    }
    return {
        "invariant": "Continuous Becoming",
        "append_only": True,
        "ledgers": described,
        "ledger_count": len(ledgers),
        "records_total": sum(ledgers.values()),
        "note": "Every ledger is append-only; the histories compound and are never rewritten.",
        "status": "continues",
    }
