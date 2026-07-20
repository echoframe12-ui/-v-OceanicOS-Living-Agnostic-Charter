"""Generate an OpenAPI 3 document from Flask's live route table.

Fifteen rounds of endpoints made a hand-maintained API spec impossible to keep
honest — it drifts the moment the next route lands. So the API describes itself:
this walks the route map and produces a machine-readable spec that is accurate by
construction. There is nothing to remember to update, because there is nothing
maintained by hand — the routes are the source of truth.
"""
from __future__ import annotations

import re
from typing import Any

_SEGMENT = re.compile(r"<(?:(?P<conv>[^:>]+):)?(?P<name>[^>]+)>")
_CONVERTER_TYPES = {"int": "integer", "float": "number", "string": "string", "path": "string"}
_SKIP_METHODS = {"HEAD", "OPTIONS"}


def _path_and_params(rule: str) -> tuple[str, list[dict[str, Any]]]:
    """Convert a Flask rule to an OpenAPI path plus its path parameters."""
    params: list[dict[str, Any]] = []
    for match in _SEGMENT.finditer(rule):
        name = match.group("name")
        conv = match.group("conv") or "string"
        params.append(
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": _CONVERTER_TYPES.get(conv, "string")},
            }
        )
    openapi_path = _SEGMENT.sub(lambda m: "{" + m.group("name") + "}", rule)
    return openapi_path, params


def _summary(view: Any, endpoint: str) -> str:
    doc = (getattr(view, "__doc__", None) or "").strip()
    return doc.splitlines()[0].strip() if doc else endpoint


def generate(
    url_map: Any,
    view_functions: dict[str, Any],
    *,
    title: str,
    version: str,
    description: str = "",
) -> dict[str, Any]:
    """Build an OpenAPI 3.0.3 document from a Werkzeug url_map and view functions.

    Documents every route (bar `static`): its path, methods, a summary from the
    view's docstring, and typed path parameters. Request/response schemas are a
    deliberate later step — this guarantees the *surface* is always complete and
    current, which is the drift problem worth solving first.
    """
    paths: dict[str, Any] = {}
    for rule in url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        openapi_path, params = _path_and_params(rule.rule)
        item = paths.setdefault(openapi_path, {})
        summary = _summary(view_functions.get(rule.endpoint), rule.endpoint)
        for method in sorted(rule.methods - _SKIP_METHODS):
            operation: dict[str, Any] = {
                "operationId": f"{method.lower()}_{rule.endpoint}",
                "summary": summary,
                "responses": {"200": {"description": "Success"}},
            }
            if params:
                operation["parameters"] = params
            item[method.lower()] = operation
    return {
        "openapi": "3.0.3",
        "info": {"title": title, "version": version, "description": description},
        "paths": paths,
    }
