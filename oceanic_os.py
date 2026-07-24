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
import sys
import tempfile
from pathlib import Path
from typing import Any

import anchor
import identity
import models
import readiness
import status_digest
from datetime import datetime, timezone
from attestation import CONFIDENCE_THRESHOLD, AttestationEngine
from cvi_history import CviHistory
from held_reviews import HeldReviewLog, sla_status
from models import ModelAdapter, ModelRouter

DEFAULT_MANIFEST = "boot/init.v1"


def _db_path() -> str:
    return os.getenv("OCEANICOS_DB", "oceanicos.db")


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
        "identity": identity.as_list(),
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
        "  identity   :",
        *("    " + line for line in identity.render().splitlines()),
        "  Ghost Processes spawned. The compiler has read the Charter.",
        f"  exit: {report['exit']} ({report['status']}…)",
    ]
    return "\n".join(lines)


def _cmd_boot(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="oceanic-os boot", description=__doc__)
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


def _emit(report: dict[str, Any], as_json: bool, render) -> None:
    print(json.dumps(report, indent=2) if as_json else render(report))


def _cmd_verify(argv: list[str]) -> int:
    """Verify the configured ledger offline — exit non-zero if the chain is broken."""
    parser = argparse.ArgumentParser(prog="oceanic-os verify")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = AttestationEngine(_db_path()).verify()
    _emit(
        report,
        args.json,
        lambda r: f"chain: {'INTACT' if r['intact'] else 'BROKEN @ ' + str(r.get('broken_at'))}"
        f" · length {r['length']}"
        f" · {'trustworthy' if r.get('trustworthy') else ('checkpointed' if r.get('checkpointed') else 'unsealed')}",
    )
    return 0 if report["intact"] else 1


def _cmd_stats(argv: list[str]) -> int:
    """Print the ledger's aggregate statistics."""
    parser = argparse.ArgumentParser(prog="oceanic-os stats")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = AttestationEngine(_db_path()).stats()
    _emit(
        report,
        args.json,
        lambda r: f"attestations: {r['total']} ({r['attested']} attested, {r['held']} held,"
        f" ratio {r['held_ratio']}) · mean conf {r['mean_confidence']}",
    )
    return 0


def _cmd_ready(argv: list[str]) -> int:
    """Probe the operational dependencies — exit non-zero if not ready."""
    parser = argparse.ArgumentParser(prog="oceanic-os ready")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = readiness.probe(_db_path(), os.getenv("OCEANICOS_WORKSPACE", "workspace"))
    _emit(report, args.json, lambda r: f"ready: {r['ready']} · checks {r['checks']}")
    return 0 if report["ready"] else 1


def _held_health(engine: AttestationEngine, review_log: HeldReviewLog, released) -> tuple[int, int]:
    """Held-queue health from the local ledger — pending count and SLA breaches.

    Computed exactly as the service does (released items credited, the same
    `sla_status` and `OCEANICOS_HELD_SLA_SECONDS`), shared by `gate` and `digest`
    so neither drifts from `/metrics` or `/status.json`.
    """
    sla_seconds = int(os.getenv("OCEANICOS_HELD_SLA_SECONDS", "86400"))
    held = engine.held()
    pending = [att for att in held if att["id"] not in released]
    breached = sum(
        1
        for att in held
        if sla_status(
            att["created_at"], review_log.latest_for(att["id"]), sla_seconds
        ).get("sla_breached")
    )
    return len(pending), breached


def _cmd_digest(argv: list[str]) -> int:
    """Emit or verify a signed status digest — the portable posture, offline.

    With no arguments, builds a signed digest from the configured ledger (the
    same canonical payload the `/status/digest` endpoint signs) and prints it.
    With `--verify FILE` (or `-` for stdin), checks a digest's operator-key
    signature and exits non-zero if it does not verify. The offline half of the
    self-report loop: produce here, hand it to an auditor, verify anywhere.
    """
    parser = argparse.ArgumentParser(prog="oceanic-os digest")
    parser.add_argument(
        "--verify", metavar="FILE", default=None,
        help="verify a digest file (or '-' for stdin) instead of emitting one",
    )
    parser.add_argument("--key", default=None, help="signing key (default OCEANICOS_SIGNING_KEY)")
    args = parser.parse_args(argv)
    key = args.key or os.getenv("OCEANICOS_SIGNING_KEY") or None

    if args.verify is not None:
        raw = sys.stdin.read() if args.verify == "-" else open(args.verify).read()
        digest = json.loads(raw)
        valid = status_digest.verify(digest, digest.get("signature"), key)
        print(
            f"digest: {'VALID' if valid else 'INVALID'}"
            f" · posture {digest.get('posture')} · {digest.get('generated_at')}"
        )
        return 0 if valid else 1

    engine = AttestationEngine(_db_path())
    review_log = HeldReviewLog(_db_path())
    released = review_log.released_ids()
    held_pending, held_breached = _held_health(engine, review_log, released)
    cp = engine.latest_checkpoint()
    payload = status_digest.build_payload(
        verify=engine.verify(),
        cvi_value=engine.cvi(released_ids=released)["cvi"],
        sourced_ratio=engine.stats()["sourced_ratio"],
        held_pending=held_pending,
        held_breached=held_breached,
        checkpoint_head=cp["head_hash"] if cp else None,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    signature = status_digest.sign(key, payload) if key else None
    print(json.dumps({**payload, "signed": signature is not None, "signature": signature}, indent=2))
    return 0


def _cmd_gate(argv: list[str]) -> int:
    """A CI trust gate: pass only if the ledger meets the required posture.

    Unlike `verify` (chain integrity alone), this is a policy gate — it can also
    require the signed-checkpoint `trustworthy` state and a minimum CVI, so a
    build fails when trust *regresses*, not only when the chain breaks. Released
    held items are credited to the CVI, matching what the service reports. Prints
    PASS/FAIL with the reasons and exits 0 (pass) or 1 (fail).
    """
    parser = argparse.ArgumentParser(prog="oceanic-os gate")
    parser.add_argument(
        "--min-cvi", type=float, default=None,
        help="fail if the CVI is below this floor (0-1)",
    )
    parser.add_argument(
        "--require-trustworthy", action="store_true",
        help="fail unless the signed checkpoint verifies (default: require only an intact chain)",
    )
    parser.add_argument(
        "--min-sourced", type=float, default=None,
        help="fail if the fraction of attestations citing a source is below this floor (0-1)",
    )
    parser.add_argument(
        "--max-held-pending", type=int, default=None,
        help="fail if more than this many held attestations await a steward decision",
    )
    parser.add_argument(
        "--no-sla-breach", action="store_true",
        help="fail if any pending held attestation is past the review SLA",
    )
    parser.add_argument(
        "--max-cvi-drop", type=float, default=None,
        help="fail if the CVI has fallen more than this far below its recorded peak",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    engine = AttestationEngine(_db_path())
    review_log = HeldReviewLog(_db_path())
    verify = engine.verify()
    released = review_log.released_ids()
    cvi = engine.cvi(released_ids=released)
    stats = engine.stats()
    held_pending, held_breached = _held_health(engine, review_log, released)

    # CVI peak from the recorded trend — the baseline a regression is measured against
    history = CviHistory(_db_path()).list()
    cvi_peak = max((point["cvi"] for point in history), default=None)

    reasons: list[str] = []
    if not verify["intact"]:
        reasons.append(f"chain broken @ {verify.get('broken_at')}")
    if args.require_trustworthy and not verify.get("trustworthy"):
        reasons.append("not trustworthy (no valid signed checkpoint)")
    if args.min_cvi is not None and cvi["cvi"] < args.min_cvi:
        reasons.append(f"cvi {cvi['cvi']} below floor {args.min_cvi}")
    if (
        args.max_cvi_drop is not None
        and cvi_peak is not None
        and cvi["cvi"] < round(cvi_peak - args.max_cvi_drop, 6)
    ):
        reasons.append(
            f"cvi {cvi['cvi']} dropped {round(cvi_peak - cvi['cvi'], 3)} "
            f"below peak {cvi_peak} (limit {args.max_cvi_drop})"
        )
    if args.min_sourced is not None and stats["sourced_ratio"] < args.min_sourced:
        reasons.append(f"sourced_ratio {stats['sourced_ratio']} below floor {args.min_sourced}")
    if args.max_held_pending is not None and held_pending > args.max_held_pending:
        reasons.append(f"held_pending {held_pending} over limit {args.max_held_pending}")
    if args.no_sla_breach and held_breached:
        reasons.append(f"{held_breached} held attestation(s) past the review SLA")
    passed = not reasons

    report = {
        "passed": passed,
        "intact": verify["intact"],
        "trustworthy": bool(verify.get("trustworthy")),
        "cvi": cvi["cvi"],
        "cvi_peak": cvi_peak,
        "sourced_ratio": stats["sourced_ratio"],
        "held_pending": held_pending,
        "held_breached": held_breached,
        "length": verify["length"],
        "policy": {
            "require_trustworthy": args.require_trustworthy,
            "min_cvi": args.min_cvi,
            "min_sourced": args.min_sourced,
            "max_held_pending": args.max_held_pending,
            "no_sla_breach": args.no_sla_breach,
            "max_cvi_drop": args.max_cvi_drop,
        },
        "reasons": reasons,
    }
    _emit(
        report,
        args.json,
        lambda r: f"gate: {'PASS' if r['passed'] else 'FAIL'}"
        f" · cvi {r['cvi']} · sourced {r['sourced_ratio']}"
        f" · held {r['held_pending']} ({r['held_breached']} past SLA) · length {r['length']}"
        f" · {'trustworthy' if r['trustworthy'] else ('intact' if r['intact'] else 'BROKEN')}"
        + (f" · {'; '.join(r['reasons'])}" if r["reasons"] else ""),
    )
    return 0 if passed else 1


_COMMANDS = {
    "boot": _cmd_boot,
    "verify": _cmd_verify,
    "stats": _cmd_stats,
    "ready": _cmd_ready,
    "gate": _cmd_gate,
    "digest": _cmd_digest,
}


def main(argv: list[str] | None = None) -> int:
    """Dispatch to a subcommand; `boot` is the default (and back-compatible).

    A leading flag (e.g. `--boot …`) or no argument runs `boot`, so the original
    invocation still works; `verify`/`stats`/`ready` are the operator tools.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    command = "boot"
    if argv and not argv[0].startswith("-"):
        command = argv.pop(0)
    handler = _COMMANDS.get(command)
    if handler is None:
        print(f"unknown command '{command}'; choose from {sorted(_COMMANDS)}")
        return 2
    return handler(argv)


if __name__ == "__main__":
    raise SystemExit(main())
