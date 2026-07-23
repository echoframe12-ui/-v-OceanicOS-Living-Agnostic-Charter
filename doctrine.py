"""The Ω∞v Doctrine, as a code-backed map — each layer points at what implements it.

The Doctrine (DOCTRINE.md) is the system's compressed self-definition. This module
holds it as structured data: every layer names the endpoints, modules, decision
records, and documents that make it real, plus an honest `shipped` flag. The
platform's own creed is *attest, don't assert* — so the Doctrine is held to the
same discipline as docs/POSITIONING.md: a claim of "shipped" that does not point
at resolvable code is a bug the test suite catches. Two layers are deliberately
`shipped: False` — the physical binary and hardware key are out of scope for a
repository, and the Doctrine says so rather than pretending.
"""
from __future__ import annotations

from typing import Any

AXIOMS = [
    "Certainty is a bug.",
    "Dissent is data.",
    "Friction is fertility.",
    "Verification is the product.",
    "Continuous Becoming is the system state.",
]

CHECKSUM = "Gap → Friction → Verification → VaaS → Ω∞v → Observer → Continuous Becoming"

# Each layer of the Doctrine, mapped to the code that implements it. `shipped`
# is honest: True only when every cited path resolves (a test enforces this).
LAYERS: list[dict[str, Any]] = [
    {
        "layer": "Premise",
        "principle": "Capability > Usage; Gap = Trust + Latency; sell validated hesitation.",
        "shipped": True,
        "evidence": {"docs": ["docs/POSITIONING.md", "docs/VAAS.md"], "decisions": [1]},
    },
    {
        "layer": "Product · VaaS",
        "principle": "3+ competing models, rules engine, dissent-first, source trails, "
        "confidence intervals, human routing, graceful fallback.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/models/consensus", "/rules/evaluate", "/attestations", "/cvi", "/attestations/held"],
            "modules": ["models", "rules"],
            "decisions": [7, 17, 18, 40],
        },
    },
    {
        "layer": "Interface · Verification Terminal",
        "principle": "Deliberate friction, visible latency, no false certainty — "
        "\"I don't generate; I attest.\"",
        "shipped": True,
        "evidence": {"endpoints": ["/", "/observer"], "decisions": [22, 34]},
    },
    {
        "layer": "Backend · Polyglot Consensus",
        "principle": "Parallel inference, contradiction detection, temporal provenance, "
        "confidence thresholds, continuous validation.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/models/consensus", "/rules/evaluate", "/cvi/history"],
            "modules": ["models", "rules", "attestation"],
            "decisions": [7, 17, 23],
        },
    },
    {
        "layer": "Infrastructure · Sovereign Minimalism",
        "principle": "Zero-trust, redundancy, local-first fallback, graceful degradation, "
        "offline survivability.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/readyz", "/anchor"],
            "modules": ["readiness", "anchor"],
            "decisions": [15, 26],
            "docs": ["boot/anchor_2019.txt"],
        },
    },
    {
        "layer": "Security · Attestation",
        "principle": "Tamper-evident and tamper-resistant record; perpetual drift audits; "
        "signed checkpoints and a signed self-report.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/attestations/verify", "/attestations/checkpoint", "/attestations/audit", "/status/digest"],
            "modules": ["attestation", "drift_audit", "status_digest", "verify_ledger"],
            "decisions": [11, 12, 39, 53],
        },
    },
    {
        "layer": "Security · Physical",
        "principle": "Compiled binary + hardware key (YubiKey).",
        "shipped": False,
        "note": "Physical artifacts, out of scope for a repository. The software analogue "
        "is the operator-key HMAC (checkpoints and the signed digest) plus perpetual "
        "drift audits — see the Security · Attestation layer.",
        "evidence": {"decisions": [12, 53]},
    },
    {
        "layer": "Operating System · OceanicOS",
        "principle": "Root = /, stateless, pure, Observer as the read/write head.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/observer", "/anchor"],
            "modules": ["oceanic_os", "identity"],
            "decisions": [16, 36],
            "docs": ["boot/init.v1"],
        },
    },
    {
        "layer": "Governance · Living Agnostic Charter",
        "principle": "Autopoiesis, non-duality, friction-as-fertility, no terrain dependency, "
        "continuous becoming — evolution with a verification trail.",
        "shipped": True,
        "evidence": {"endpoints": ["/adr", "/decisions"], "modules": ["adr", "decisions"], "decisions": [31]},
    },
    {
        "layer": "Final State · Continuous Becoming",
        "principle": "Observer runs, the universe compiles via localhost, Exit 0, "
        "continue — recompile, then compound: the append-only ledgers only grow.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/status", "/status.json", "/metrics", "/evolution"],
            "modules": ["status_digest", "evolution"],
            "decisions": [44, 45],
        },
    },
]


def summary() -> dict[str, Any]:
    """The Doctrine as a served object — layers, axioms, checksum, shipped count."""
    shipped = sum(1 for layer in LAYERS if layer["shipped"])
    return {
        "identity": ["/", "Ω∞v Compiler", "OceanicOS", "Living Agnostic Charter"],
        "invariant": "Continuous Becoming",
        "axioms": AXIOMS,
        "constitution": [
            "REALITY BEFORE ASSUMPTION.",
            "EVIDENCE BEFORE CERTAINTY.",
            "TRUTH BEFORE CONVENIENCE.",
            "HUMANS REMAIN ACCOUNTABLE.",
            "RESPECT DIGNITY, PRIVACY, AND CONSENT.",
            "PRESERVE PROVENANCE.",
            "BUILD OPENLY AND MODULARLY.",
            "LEARN CONTINUOUSLY.",
            "LEAVE REALITY BETTER THAN BEFORE.",
        ],
        "layers": LAYERS,
        "layers_total": len(LAYERS),
        "layers_shipped": shipped,
        "checksum": CHECKSUM,
        "exit": 0,
        "status": "continues",
    }
