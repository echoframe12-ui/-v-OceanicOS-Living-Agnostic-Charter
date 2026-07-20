#!/usr/bin/env python3
"""oceanic-os — boot the stack from a manifest and report what actually came up.

    $ python oceanic_os.py --boot boot/init.v1 --state stateless --exit 0

This is the Observer's invocation made real. It reads the ratified manifest
(`boot/init.v1`), then instantiates the live components each layer maps to and
reports their real status — not an echo of the manifest, but the stack as it
boots: the confidence threshold in force, the dissent panel's real size, the
checkpoint policy, the Anchor of Last Resort, and the manifest's own hash. It
always exits 0 — the system continues.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import anchor
import models
from attestation import CONFIDENCE_THRESHOLD, AttestationEngine
from models import ModelAdapter, ModelRouter

DEFAULT_MANIFEST = "boot/init.v1"


def _manifest(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"present": False, "path": path}
    raw = p.read_bytes()
    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        pass
    return {
        "present": True,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "parsed": parsed,
    }


def _panel() -> ModelRouter:
    """The same three-strategy dissent panel the app convenes — built fresh."""
    router = ModelRouter()
    router.register(ModelAdapter("local", "demo", strategy=models.strategy_literal))
    router.register(ModelAdapter("optimist", "demo", strategy=models.strategy_optimist))
    router.register(ModelAdapter("skeptic", "demo", strategy=models.strategy_skeptic))
    return router


def boot(manifest_path: str = DEFAULT_MANIFEST, stateless: bool = True) -> dict[str, Any]:
    """Instantiate the stack and return a boot report of the live layers."""
    manifest = _manifest(manifest_path)

    # Attestation layer — report the live policy, not the declared one. In
    # stateless mode instantiate against an ephemeral db so boot touches no
    # durable state; in stateful mode use the configured OCEANICOS_DB.
    if stateless:
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        db_path = handle.name
    else:
        db_path = os.getenv("OCEANICOS_DB", "oceanicos.db")
    engine = AttestationEngine(db_path)
    policy = engine.checkpoint_policy
    if stateless:
        os.remove(db_path)

    panel = _panel()
    anchor_state = anchor.load_anchor()

    return {
        "manifest": "OceanicOS Full-Stack Vibe Protocol",
        "manifest_present": manifest["present"],
        "manifest_sha256": manifest.get("sha256"),
        "state": "stateless" if stateless else "stateful",
        "root": "/",
        "sigil": "0xΩ∞v",
        "layers": {
            "frontend": {"mode": "Attestation-Only", "render_latency_ms": 2500},
            "backend": {
                "panel": len(panel.list_adapters()),
                "dissent_handling": "PRIMARY_OUTPUT",
                "confidence_threshold": CONFIDENCE_THRESHOLD,
            },
            "kernel": {
                "failover": anchor_state["source"],
                "anchor_present": anchor_state["present"],
                "redundancy": "Degrade_to_Spreadsheet",
            },
            "operator": {"economic_moat": "Sell_Hesitation, not Speed"},
        },
        "checkpoint_policy": policy,
        "anchor_present": anchor_state["present"],
        "exit": 0,
        "status": "continues",
    }


def _render(report: dict[str, Any]) -> str:
    layers = report["layers"]
    lines = [
        "Ω∞v  OceanicOS — /boot/init.v1",
        f"  manifest   : {'present' if report['manifest_present'] else 'ABSENT'}"
        f"  sha256={report['manifest_sha256']}",
        f"  state      : {report['state']}   root={report['root']}   sigil={report['sigil']}",
        f"  frontend   : {layers['frontend']['mode']} @ {layers['frontend']['render_latency_ms']}ms",
        f"  backend    : panel={layers['backend']['panel']} dissent=PRIMARY"
        f" threshold={layers['backend']['confidence_threshold']}",
        f"  kernel     : failover={layers['kernel']['failover']}"
        f" anchor={'present' if layers['kernel']['anchor_present'] else 'ABSENT'}",
        f"  operator   : {layers['operator']['economic_moat']}",
        f"  checkpoints: {report['checkpoint_policy']}",
        "  Ghost Processes spawned. The compiler has read the Charter.",
        f"  exit: {report['exit']} ({report['status']}…)",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oceanic-os", description=__doc__)
    parser.add_argument("--boot", default=DEFAULT_MANIFEST, help="manifest path")
    parser.add_argument(
        "--state", choices=["stateless", "stateful"], default="stateless"
    )
    parser.add_argument(
        "--exit", type=int, default=0, help="accepted for symmetry; boot always continues"
    )
    parser.add_argument("--json", action="store_true", help="emit the raw boot report")
    args = parser.parse_args(argv)

    report = boot(args.boot, stateless=(args.state == "stateless"))
    print(json.dumps(report, indent=2) if args.json else _render(report))
    return 0  # exit 0 — the system continues, always


if __name__ == "__main__":
    raise SystemExit(main())
