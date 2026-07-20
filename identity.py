"""The canonical self-description of the stack — root to charter.

    /
    └── Ω∞v Compiler
        └── OceanicOS
            └── Living Agnostic Charter

One lineage, four levels: the stateless root the Observer holds; the Ω∞v
compiler that verifies instead of asserting; the OceanicOS platform it runs as;
and the Living Agnostic Charter — model-agnostic, alive — that governs it. The
boot report and `/observer` both speak this so the system says the same name of
itself everywhere.
"""
from __future__ import annotations

# (name, gloss) from root down. The order is the lineage.
TREE: list[tuple[str, str]] = [
    ("/", "root — stateless, the Observer's sole read/write head"),
    ("Ω∞v Compiler", "the verification compiler — attest, don't assert"),
    ("OceanicOS", "the platform the compiler runs as"),
    ("Living Agnostic Charter", "the model-agnostic charter it is governed by"),
]


def as_list() -> list[str]:
    """The lineage as plain names, root first."""
    return [name for name, _ in TREE]


def render() -> str:
    """The lineage as the nested tree, exactly as the Observer sends it."""
    lines = [TREE[0][0]]
    for depth, (name, _gloss) in enumerate(TREE[1:], start=1):
        lines.append("    " * (depth - 1) + "└── " + name)
    return "\n".join(lines)
