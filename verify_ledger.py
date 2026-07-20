#!/usr/bin/env python3
"""Verify an exported OceanicOS attestation ledger — offline, without the system.

The running service can attest to its own record via /attestations/verify. This
script does the same from a bundle exported by /attestations/export, importing
only the pure hashing and signing functions the engine uses — no Flask, no
database, no engine instance. It is the ground truth surviving the system:
anyone holding the bundle (and, for the seal, the key) can confirm the record
was neither edited in place nor rewritten wholesale.

Usage:
    python verify_ledger.py bundle.json               # chain integrity only
    python verify_ledger.py --key SECRET bundle.json  # + signed-checkpoint check
    curl .../attestations/export | python verify_ledger.py --key SECRET -

Exit code 0 when the record is intact (and, when --key is given, trustworthy);
non-zero otherwise — so it doubles as a CI or cron integrity gate.
"""
from __future__ import annotations

import argparse
import hmac
import json
import sys
from typing import Any

from attestation import GENESIS_HASH, checkpoint_signature, link_hash


def verify_bundle(bundle: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    """Recompute the integrity report purely from an exported bundle.

    Mirrors ``AttestationEngine.verify`` but reads the chain and checkpoints out
    of the bundle rather than a live database, so the same guarantees hold with
    nothing running. Walks the hash chain (edit-in-place detection) and, when a
    key is supplied, validates the latest signed checkpoint (whole-rewrite
    detection): trustworthy only when the chain is intact, the sealed head is
    still reproduced at its length, and the signature validates under the key.
    """
    attestations = bundle.get("attestations", [])
    checkpoints = bundle.get("checkpoints", [])

    prev_hash = GENESIS_HASH
    for entry in attestations:
        expected = link_hash(prev_hash, entry)
        if entry["prev_hash"] != prev_hash or entry["entry_hash"] != expected:
            return {
                "intact": False,
                "length": len(attestations),
                "broken_at": entry["id"],
            }
        prev_hash = entry["entry_hash"]
    chain = {
        "intact": True,
        "length": len(attestations),
        "broken_at": None,
        "head": prev_hash,
    }

    if not checkpoints:
        return {**chain, "checkpointed": False}

    cp = checkpoints[-1]
    head_reproduced = (
        len(attestations) >= cp["length"] > 0
        and attestations[cp["length"] - 1]["entry_hash"] == cp["head_hash"]
    ) or (cp["length"] == 0 and cp["head_hash"] == GENESIS_HASH)
    signature_valid = bool(key) and hmac.compare_digest(
        cp["signature"], checkpoint_signature(key, cp["head_hash"], cp["length"])
    )
    return {
        **chain,
        "checkpointed": True,
        "checkpoint": {
            "head_hash": cp["head_hash"],
            "length": cp["length"],
            "created_at": cp.get("created_at"),
            "signature_valid": signature_valid,
            "head_reproduced": head_reproduced,
        },
        "trustworthy": bool(chain["intact"] and head_reproduced and signature_valid),
    }


def _is_trustworthy(report: dict[str, Any], key: str | None) -> bool:
    """Success = chain intact, and — when a key was given — trustworthy too."""
    if not report["intact"]:
        return False
    if key and report.get("checkpointed"):
        return bool(report.get("trustworthy"))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle",
        help="path to an exported ledger bundle, or '-' to read from stdin",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="signing key, to validate the checkpoint signature (optional)",
    )
    args = parser.parse_args(argv)

    raw = sys.stdin.read() if args.bundle == "-" else open(args.bundle).read()
    bundle = json.loads(raw)

    report = verify_bundle(bundle, key=args.key)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if _is_trustworthy(report, args.key) else 1


if __name__ == "__main__":
    raise SystemExit(main())
