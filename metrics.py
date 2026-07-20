"""Render platform state in the Prometheus text exposition format.

Every number the platform tracks — CVI, held counts, SLA breaches, chain state —
already exists; it was just scattered across JSON endpoints. This turns a flat
list of metrics into the one format every monitoring stack scrapes, so OceanicOS
is observable by ordinary tooling without a bespoke integration. Pure formatting:
the caller assembles the live snapshot, this renders it.
"""
from __future__ import annotations

from typing import Any

# Flask appends "; charset=utf-8" for text/* mimetypes, yielding the full
# Prometheus content type — so it's omitted here to avoid a doubled charset.
CONTENT_TYPE = "text/plain; version=0.0.4"


def _format_value(value: Any) -> str:
    # bool is a subclass of int, so it must be checked first: True -> 1, False -> 0
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def render(metrics: list[dict[str, Any]]) -> str:
    """Format `[{name, help, value, type?}]` as Prometheus exposition text.

    Each metric emits its HELP and TYPE header lines followed by the sample.
    `type` defaults to `gauge` — every platform number here is a current
    reading, not a monotonic counter.
    """
    lines: list[str] = []
    for metric in metrics:
        name = metric["name"]
        lines.append(f"# HELP {name} {metric['help']}")
        lines.append(f"# TYPE {name} {metric.get('type', 'gauge')}")
        lines.append(f"{name} {_format_value(metric['value'])}")
    return "\n".join(lines) + "\n"
