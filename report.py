"""A composed, human-readable trust report — the platform's state as one document.

`/status.json` is for machines; this is for a person. It synthesizes the same
posture, the trust dimensions (confidence and its peak, evidence, dissent,
integrity), the held queue, the seal and the last audit, and the compounding
footprint into a single Markdown page a stakeholder can read or attach to a
release. Pure: `render` takes the already-assembled structures and formats them,
so it composes existing reads and states no fact the surfaces do not already.
"""
from __future__ import annotations

from typing import Any


def _pct(value: float) -> str:
    return f"{round(value * 100)}%"


def render(snapshot: dict[str, Any], footprint: dict[str, Any], dissent: dict[str, Any]) -> str:
    """Render the trust report as Markdown from a status snapshot, footprint, and dissent stats."""
    verify = snapshot["verify"]
    cvi = snapshot["cvi"]
    lo, hi = cvi["confidence_interval"]
    peak = snapshot["cvi_peak"]
    peak_note = f"peak {peak:.2f} (▼{peak - cvi['cvi']:.2f})" if peak > cvi["cvi"] else "at peak"

    if not verify["intact"]:
        chain = f"BROKEN at #{verify.get('broken_at')}"
    elif verify.get("trustworthy"):
        chain = f"intact · {verify['length']} links · sealed head reproduced & signed"
    else:
        chain = f"intact · {verify['length']} links · not yet sealed to trustworthy"

    cp = snapshot.get("checkpoint")
    audit = snapshot.get("audit")
    rows = [
        ("Chain", chain),
        ("CVI", f"{cvi['cvi']:.2f} · confidence {lo:.2f}–{hi:.2f} · {peak_note}"),
        ("Source coverage", _pct(snapshot["sourced_ratio"])),
        ("Dissent", f"rate {_pct(dissent['dissent_rate'])} · mean split {dissent['mean_dissent_score']} ({dissent['evaluations']} evals)"),
        ("Held queue", f"{snapshot['held_pending']} pending · {snapshot['held_breached']} past SLA"),
        ("Latest checkpoint", f"length {cp['length']} · {cp['created_at']}" if cp else "none sealed yet"),
        ("Latest drift audit", (f"{'intact' if audit['intact'] else 'BROKEN'} · {audit['checked_at']}" if audit else "none recorded yet")),
    ]
    signal_table = "\n".join(f"| {k} | {v} |" for k, v in rows)

    ledger_rows = "\n".join(
        f"| {name.replace('_', ' ')} | {entry['count']} |"
        for name, entry in footprint["ledgers"].items()
    )

    return f"""# OceanicOS Trust Report

_Generated {snapshot['generated_at']} · threshold {snapshot['threshold']} · attest, don't assert_

## Posture: {snapshot['posture']}

| Signal | Value |
| --- | --- |
{signal_table}

## Compounding footprint

{footprint['records_total']} records across {footprint['ledger_count']} append-only ledgers — the histories compound.

| Ledger | Count |
| --- | --- |
{ledger_rows}

---

Exit 0. Continues…
"""
