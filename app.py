import csv
import hashlib
import io
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, Response, g, jsonify, render_template, request

import requestlog

import adr
import anchor
import badge
import identity
import metrics
import openapi
import readiness
from agent import AgentLoop
from cvi_history import CviHistory
from drift_audit import DriftAuditLog
from verify_ledger import verify_bundle
from artifacts import ArtifactRegistry
from attestation import AttestationEngine, CONFIDENCE_THRESHOLD
from auth import ANONYMOUS, AuthRegistry
from claude_adapter import create_claude_adapter
from dashboard import Dashboard
from decisions import DecisionRegistry
import models
from models import ModelAdapter, ModelRouter
from nodes import NodeRegistry
from planner import Planner
from plugins import PluginRegistry
import quotas
from held_reviews import HeldReviewLog, VERDICTS, sla_status
from rules import RulesAdapter, RulesEngine
from usage import UsageLog
from review import ReviewEngine
from server import OceanicOSService
from state import StateSnapshot
from universal_builder import UniversalBuilder
from workflows import WorkflowEngine

app = Flask(__name__)

access_logger = logging.getLogger("oceanicos.access")
if not access_logger.handlers:
    # Emit one JSON object per line to stderr; the message is already serialized,
    # so the formatter passes it through untouched. propagate=False keeps it out
    # of the root logger (no duplicate lines).
    _access_handler = logging.StreamHandler()
    _access_handler.setFormatter(logging.Formatter("%(message)s"))
    access_logger.addHandler(_access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False


@app.before_request
def _assign_request_id():
    g.request_id = requestlog.clean_request_id(request.headers.get("X-Request-ID"))
    g.start_time = time.perf_counter()


@app.after_request
def _log_access(response):
    start = getattr(g, "start_time", None)
    latency_ms = round((time.perf_counter() - start) * 1000, 2) if start else 0.0
    request_id = getattr(g, "request_id", "")
    response.headers["X-Request-ID"] = request_id
    access_logger.info(
        json.dumps(
            requestlog.access_record(
                request_id,
                request.method,
                request.path,
                response.status_code,
                getattr(g, "actor", None),
                latency_ms,
            )
        )
    )
    return response


service = OceanicOSService()
workflow_engine = WorkflowEngine()
planner = Planner()
model_router = ModelRouter()
model_router.register(
    ModelAdapter("local", "demo", strategy=models.strategy_literal)
)
model_router.register(
    ModelAdapter(
        "reasoning",
        "demo",
        keywords=["plan", "build", "design", "charter"],
        strategy=models.strategy_optimist,
    )
)
model_router.register(
    ModelAdapter(
        "skeptic",
        "demo",
        keywords=["plan", "verify", "charter", "attest"],
        strategy=models.strategy_skeptic,
    )
)
claude_adapter = create_claude_adapter(keywords=["claude"])
if claude_adapter is not None:
    model_router.register(claude_adapter)
# The deterministic anchor: a rules engine that always weighs in and explains
# itself — "3 competing LLMs + 1 rules engine" from the manifest, made real.
rules_engine = RulesEngine()
model_router.register(RulesAdapter(rules_engine))
agent_loop = AgentLoop()
state_snapshot = StateSnapshot()
review_engine = ReviewEngine()
decision_registry = DecisionRegistry()
artifact_registry = ArtifactRegistry()
dashboard = Dashboard()
plugin_registry = PluginRegistry()
attestation_engine = AttestationEngine(
    str(service.db_path),
    signing_key=os.getenv("OCEANICOS_SIGNING_KEY", ""),
    checkpoint_every=int(os.getenv("OCEANICOS_CHECKPOINT_EVERY", "0")),
)
node_registry = NodeRegistry()
auth_registry = AuthRegistry()
usage_log = UsageLog(str(service.db_path))
held_review_log = HeldReviewLog(str(service.db_path))
cvi_history = CviHistory(str(service.db_path))
drift_audit_log = DriftAuditLog(str(service.db_path))
# Time-to-decision SLA for held attestations (seconds). 0 disables breach flags.
HELD_SLA_SECONDS = int(os.getenv("OCEANICOS_HELD_SLA_SECONDS", "86400"))


def _snapshot_cvi(actor: str | None = None) -> None:
    """Record the platform CVI when it moves, and the actor's own when given.

    The platform series is always updated; when a named actor drove the change
    (a build), their personal CVI trend is recorded too, so `/me/cvi/history`
    reflects that actor's verification quality over time (round 36).
    """
    released = held_review_log.released_ids()
    cvi_history.record_if_changed(attestation_engine.cvi(released_ids=released))
    if actor and actor != ANONYMOUS:
        cvi_history.record_if_changed(
            attestation_engine.cvi(actor=actor, released_ids=released), actor=actor
        )
app.config["REQUIRE_AUTH"] = os.getenv("OCEANICOS_REQUIRE_AUTH", "0") == "1"
app.config["AUTH_REGISTRY"] = auth_registry
builder = UniversalBuilder(
    service=service,
    planner=planner,
    workflow_engine=workflow_engine,
    model_router=model_router,
    agent_loop=agent_loop,
    state_snapshot=state_snapshot,
    review_engine=review_engine,
    decision_registry=decision_registry,
    artifact_registry=artifact_registry,
    dashboard=dashboard,
    plugin_registry=plugin_registry,
    attestation_engine=attestation_engine,
)


@app.errorhandler(KeyError)
def handle_not_found(error):
    return jsonify({"error": str(error).strip("'\"")}), 404


@app.errorhandler(ValueError)
def handle_bad_request(error):
    return jsonify({"error": str(error)}), 400


def _current_user() -> dict:
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else None
    user = auth_registry.authenticate(token)
    if user is None:
        return {"username": ANONYMOUS, "role": "anonymous", "tier": quotas.DEFAULT_TIER}
    return user


def _current_actor() -> str:
    return _current_user()["username"]


def _windowed_quota(actor: str, tier: str) -> dict:
    """A tier's build quota measured over the rolling usage window."""
    used, oldest = usage_log.count_in_window(actor, "build", quotas.WINDOW_SECONDS)
    resets_at = None
    if oldest is not None:
        resets_at = (
            datetime.fromisoformat(oldest) + timedelta(seconds=quotas.WINDOW_SECONDS)
        ).isoformat()
    return quotas.quota_status(
        tier, used, window_seconds=quotas.WINDOW_SECONDS, resets_at=resets_at
    )


def _rate_limit_headers(status: dict, now: datetime | None = None) -> dict[str, str]:
    """Standard rate-limit headers from a quota status.

    Finite tiers emit `X-RateLimit-Limit`/`-Remaining` (and `-Reset` as a unix
    timestamp once the window has an oldest build to age out). An exceeded quota
    adds `Retry-After` in seconds. Unlimited tiers (sovereign) emit nothing —
    there is no ceiling to report.
    """
    if status["limit"] is None:
        return {}
    now = now or datetime.now(timezone.utc)
    headers = {
        "X-RateLimit-Limit": str(status["limit"]),
        "X-RateLimit-Remaining": str(status["remaining"]),
    }
    if status["resets_at"]:
        reset = datetime.fromisoformat(status["resets_at"])
        headers["X-RateLimit-Reset"] = str(int(reset.timestamp()))
        if status["exceeded"]:
            headers["Retry-After"] = str(max(0, int((reset - now).total_seconds())))
    return headers


def require_auth(view):
    """Attribute every request to an actor; enforce a token when locked.

    Attribution is always on (g.actor / g.role). Enforcement (401 without a
    valid token) applies only when app.config['REQUIRE_AUTH'] is set.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _current_user()
        g.actor = user["username"]
        g.role = user["role"]
        g.tier = user["tier"]
        if app.config.get("REQUIRE_AUTH") and g.actor == ANONYMOUS:
            return jsonify({"error": "unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapped


def require_admin(view):
    """Stewardship gate: cross-actor views require an admin token.

    Members stay scoped to their own slice; only an accountable steward
    sees across actors — transparency for governance, not surveillance.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _current_user()
        g.actor = user["username"]
        g.role = user["role"]
        g.tier = user["tier"]
        if g.role != "admin":
            return jsonify({"error": "admin role required"}), 403
        return view(*args, **kwargs)

    return wrapped


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify(service.health())


@app.route("/readyz", methods=["GET"])
def readyz():
    """Readiness probe — are the dependencies reachable, not just the process alive?

    Checks the database and workspace (the operational dependencies) and reports
    chain integrity as context. Returns 503 when a dependency is unavailable so
    an orchestrator keeps the instance out of rotation until it recovers.
    """
    report = readiness.probe(service.db_path, os.getenv("OCEANICOS_WORKSPACE", "workspace"))
    report["chain_intact"] = attestation_engine.verify_chain()["intact"]
    return jsonify(report), (200 if report["ready"] else 503)


@app.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """The API describes itself — OpenAPI generated from the live route table."""
    return jsonify(
        openapi.generate(
            app.url_map,
            app.view_functions,
            title="OceanicOS VaaS API",
            version="1.0",
            description="Verification-as-a-Service — attest, don't assert. "
            "Spec generated from the live routes, always current.",
        )
    )


@app.route("/plans", methods=["POST"])
def create_plan():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    return jsonify(service.create_plan(task))


@app.route("/memory", methods=["POST"])
@require_auth
def store_memory():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.store_memory(payload, actor=g.actor))


@app.route("/memory", methods=["GET"])
def search_memory():
    query = request.args.get("query", "")
    actor = request.args.get("actor")
    return jsonify(service.search_memory(query, actor=actor))


@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify(service.list_tools())


@app.route("/tools/<name>", methods=["POST"])
@require_auth
def invoke_tool(name: str):
    payload = request.get_json(silent=True) or {}
    return jsonify(service.invoke_tool(name, payload))


@app.route("/workflows", methods=["POST"])
def create_workflow():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    steps = payload.get("steps", [])
    return jsonify(workflow_engine.create_workflow(name, steps))


@app.route("/workflows/<name>", methods=["GET"])
def get_workflow(name: str):
    return jsonify(workflow_engine.get_workflow(name))


@app.route("/workflows/<name>/execute", methods=["POST"])
def execute_workflow(name: str):
    return jsonify(workflow_engine.execute_workflow(name))


@app.route("/plans/execute", methods=["POST"])
def execute_planner():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    context = payload.get("context")
    return jsonify(planner.plan(task, context))


@app.route("/plans/trace", methods=["GET"])
def planner_trace():
    return jsonify(planner.get_trace())


@app.route("/models", methods=["GET"])
def list_models():
    return jsonify(model_router.list_adapters())


@app.route("/builds", methods=["GET"])
def list_builds():
    actor = request.args.get("actor")
    return jsonify(service.list_builds(actor=actor))


@app.route("/models/route", methods=["POST"])
def route_model():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    return jsonify(model_router.route(prompt))


@app.route("/models/consensus", methods=["POST"])
@require_auth
def model_consensus():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    # panel of 4: the three model heuristics plus the rules engine anchor
    return jsonify(model_router.route_all(prompt, panel=4))


@app.route("/rules/evaluate", methods=["POST"])
def rules_evaluate():
    """The rules engine's explainable verdict — which rules fired, and why.

    The panel member you can audit: unlike the model heuristics, this returns
    the named rules that triggered a revise and the reason each exists.
    """
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    return jsonify(rules_engine.evaluate(prompt))


@app.route("/attestations", methods=["GET"])
def list_attestations():
    """List the record, optionally filtered.

    Query params: actor, status (attested|held), min_confidence, max_confidence,
    subject (substring), since (ISO timestamp), limit. No params returns the
    whole record, so existing callers are unaffected.
    """
    args = request.args
    status = args.get("status")
    if status is not None and status not in ("attested", "held"):
        return jsonify({"error": "status must be 'attested' or 'held'"}), 400
    try:
        min_conf = args.get("min_confidence", type=float) if "min_confidence" in args else None
        max_conf = args.get("max_confidence", type=float) if "max_confidence" in args else None
        limit = args.get("limit", type=int) if "limit" in args else None
    except (TypeError, ValueError):
        return jsonify({"error": "min_confidence/max_confidence must be numbers, limit an integer"}), 400
    # request.args.get(type=...) returns None on a parse failure rather than raising
    for name, value in (("min_confidence", min_conf), ("max_confidence", max_conf), ("limit", limit)):
        if name in args and value is None:
            return jsonify({"error": f"{name} is not a valid number"}), 400
    return jsonify(
        attestation_engine.search(
            actor=args.get("actor"),
            status=status,
            min_confidence=min_conf,
            max_confidence=max_conf,
            subject_contains=args.get("subject"),
            since=args.get("since"),
            limit=limit,
        )
    )


def _review_status(att_id: int, released: set[int]) -> str:
    if att_id in released:
        return "released"
    return "upheld" if held_review_log.latest_for(att_id) else "pending"


@app.route("/attestations/held", methods=["GET"])
@require_admin
def list_held_attestations():
    """Held items awaiting or carrying a steward's decision.

    Each held attestation is annotated with its latest review status —
    `pending`, `released`, or `upheld` — so the steward sees the queue and its
    resolutions. Stewardship view: admin only.
    """
    released = held_review_log.released_ids()
    items = []
    for att in attestation_engine.held():
        latest = held_review_log.latest_for(att["id"])
        items.append(
            {
                **att,
                "review_status": _review_status(att["id"], released),
                "latest_review": latest,
                "sla": sla_status(att["created_at"], latest, HELD_SLA_SECONDS),
            }
        )
    return jsonify(items)


@app.route("/attestations/<int:att_id>/review", methods=["POST"])
@require_admin
def review_held_attestation(att_id: int):
    """Record a steward's decision on a held attestation — release or uphold.

    Append-only: the review references the held item and never edits it, so the
    hash chain stays intact. A documented release lifts the item out of the CVI's
    held ratio; an uphold keeps it held, on the record with a reason.
    """
    payload = request.get_json(silent=True) or {}
    verdict = payload.get("verdict", "")
    reason = (payload.get("reason") or "").strip()

    att = next((a for a in attestation_engine.list() if a["id"] == att_id), None)
    if att is None:
        return jsonify({"error": "attestation not found"}), 404
    if att["status"] != "held":
        return jsonify({"error": "attestation is not held"}), 409
    if verdict not in VERDICTS:
        return jsonify({"error": f"verdict must be one of {list(VERDICTS)}"}), 400
    if not reason:
        return jsonify({"error": "a reason is required"}), 400

    review = held_review_log.record(att_id, g.actor, verdict, reason)
    usage_log.record(g.actor, "held_review", g.tier, f"{verdict} #{att_id}")
    _snapshot_cvi()  # a release/uphold can move the CVI
    return jsonify(review)


@app.route("/attestations/<int:att_id>/reviews", methods=["GET"])
def list_held_reviews(att_id: int):
    return jsonify(held_review_log.list(att_id))


@app.route("/attestations/<int:att_id>/receipt", methods=["GET"])
def attestation_receipt(att_id: int):
    """A verification receipt for one attestation — hash, chain position, seal.

    The per-item proof: the attestation's content hash, its height in the chain,
    whether the chain is intact, and whether a signed checkpoint seals its
    position. 404 for a missing id.
    """
    receipt = attestation_engine.receipt(att_id)
    if receipt is None:
        return jsonify({"error": f"no attestation #{att_id}"}), 404
    return jsonify(receipt)


@app.route("/attestations/<int:att_id>/verify", methods=["GET"])
def verify_attestation_entry(att_id: int):
    """Verify one attestation's integrity in place — the per-item chain check.

    Recomputes this entry's link hash from its recorded fields and its
    predecessor, reporting whether it is untampered and correctly linked at its
    position. Where `/attestations/verify` checks the whole chain, this checks a
    single entry. Public, like the receipt it backs. 404 for a missing id.
    """
    result = attestation_engine.verify_entry(att_id)
    if result is None:
        return jsonify({"error": f"no attestation #{att_id}"}), 404
    return jsonify(result)


@app.route("/attestations/audit", methods=["POST"])
@require_admin
def run_drift_audit():
    """Run a drift audit — verify the ledger and record the result on the trail.

    Verifiable is not verified: this looks, and remembers having looked. A
    stewardship action; the recorded entry proves the check happened and when.
    """
    return jsonify(drift_audit_log.record(attestation_engine.verify()))


@app.route("/attestations/audits", methods=["GET"])
def list_drift_audits():
    """The drift-audit trail — proof the ledger has been verified over time."""
    limit = request.args.get("limit", type=int) if "limit" in request.args else None
    if "limit" in request.args and limit is None:
        return jsonify({"error": "limit must be an integer"}), 400
    return jsonify(drift_audit_log.list(limit=limit))


@app.route("/attestations/lookup", methods=["POST"])
def lookup_attestation():
    """Content-addressable lookup — was this exact output attested?

    Give `content` (hashed server-side) or a `sha256` directly; returns every
    attestation of that hash with its confidence and status. The way back in
    from an artifact to its attestation.
    """
    payload = request.get_json(silent=True) or {}
    if "content" in payload:
        digest = hashlib.sha256(str(payload["content"]).encode()).hexdigest()
    elif "sha256" in payload:
        digest = str(payload["sha256"])
    else:
        return jsonify({"error": "provide 'content' or 'sha256'"}), 400
    matches = attestation_engine.by_content_hash(digest)
    return jsonify({"sha256": digest, "found": bool(matches), "matches": matches})


_MAX_BATCH = 100


@app.route("/attestations/lookup/batch", methods=["POST"])
def lookup_attestations_batch():
    """Content-addressable lookup for many outputs at once.

    `contents` (each hashed server-side) and/or `sha256s` (used directly) as
    lists; returns one result per item in order. Capped at 100 items per call.
    """
    payload = request.get_json(silent=True) or {}
    contents = payload.get("contents")
    hashes = payload.get("sha256s")
    if not isinstance(contents, list) and not isinstance(hashes, list):
        return jsonify({"error": "provide 'contents' or 'sha256s' as a list"}), 400
    digests: list[str] = []
    if isinstance(contents, list):
        digests += [hashlib.sha256(str(c).encode()).hexdigest() for c in contents]
    if isinstance(hashes, list):
        digests += [str(h) for h in hashes]
    if len(digests) > _MAX_BATCH:
        return jsonify({"error": f"at most {_MAX_BATCH} items per batch"}), 400
    results = []
    for digest in digests:
        matches = attestation_engine.by_content_hash(digest)
        results.append({"sha256": digest, "found": bool(matches), "matches": matches})
    return jsonify({"count": len(results), "results": results})


@app.route("/attestations/stats", methods=["GET"])
def attestation_stats():
    """Aggregate shape of the record — totals, confidence histogram, by-actor.

    Reuses the engine's scan, so the held ratio here matches `/cvi`'s. `?actor=`
    scopes it. Public and aggregate, like `/cvi`.
    """
    return jsonify(attestation_engine.stats(actor=request.args.get("actor")))


@app.route("/attestations/verify", methods=["GET"])
def verify_attestations():
    """Confirm the ledger has not been tampered with.

    Walks the hash chain (edit-in-place detection) and checks the latest signed
    checkpoint (whole-rewrite detection): a record is trustworthy only when the
    chain is intact, its signed head is still reproduced, and the signature
    validates under the current key.
    """
    return jsonify(attestation_engine.verify())


@app.route("/attestations/verify-bundle", methods=["POST"])
def verify_supplied_bundle():
    """Verify an exported bundle a caller holds — the online twin of verify_ledger.py.

    Runs the same pure `verify_bundle` the offline verifier uses, so a client can
    check a bundle against a trusted verifier without local tooling. Chain
    integrity is always checked; the signed checkpoint validates only if this
    server holds the key the bundle was sealed with (no secret is accepted over
    the wire).
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("attestations"), list):
        return jsonify({"error": "body must be an exported ledger bundle"}), 400
    key = os.getenv("OCEANICOS_SIGNING_KEY") or None
    return jsonify(verify_bundle(payload, key=key))


@app.route("/attestations/checkpoint", methods=["POST"])
@require_admin
def checkpoint_attestations():
    """Seal the current chain head with an operator-key signature.

    Requires OCEANICOS_SIGNING_KEY. Refuses to seal an already-broken chain.
    """
    if not attestation_engine.can_sign:
        return (
            jsonify({"error": "no signing key configured (set OCEANICOS_SIGNING_KEY)"}),
            503,
        )
    try:
        sealed = attestation_engine.checkpoint()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409
    # sealing the head is a natural audit point — record one (continuous validation)
    drift_audit_log.record(attestation_engine.verify())
    return jsonify(sealed)


@app.route("/attestations/export", methods=["GET"])
def export_attestations():
    """The whole sealed attestation record as a portable, offline-verifiable bundle.

    Carries every attestation and checkpoint so the chain and its seals can be
    checked with `verify_ledger.py` — no service, no database. The ground truth
    survives the system.
    """
    return Response(
        json.dumps(attestation_engine.export(), indent=2),
        mimetype="application/json",
        headers={
            "Content-Disposition": "attachment; filename=oceanicos-attestations.json"
        },
    )


@app.route("/builds/export", methods=["GET"])
def export_builds():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "task", "context", "artifact", "stages", "actor", "created_at"])
    for build in service.list_builds():
        writer.writerow(
            [
                build["id"],
                build["task"],
                build["context"],
                build["artifact"],
                "|".join(build["stages"]),
                build["actor"],
                build["created_at"],
            ]
        )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=oceanicos-builds.csv"},
    )


@app.route("/builds/export.txt", methods=["GET"])
def export_builds_txt():
    lines = ["OCEANICOS BUILD LEDGER — PLAIN TEXT GROUND TRUTH", ""]
    for build in service.list_builds():
        lines.append(
            f"[{build['id']}] {build['created_at']} :: {build['task']} "
            f"(context: {build['context']}, actor: {build['actor']}) -> {build['artifact']} "
            f"[{'|'.join(build['stages'])}]"
        )
    if len(lines) == 2:
        lines.append("(no builds on record)")
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/cvi", methods=["GET"])
def composite_verification_index():
    return jsonify(attestation_engine.cvi(released_ids=held_review_log.released_ids()))


@app.route("/cvi/history", methods=["GET"])
def cvi_trend():
    """The CVI over time — the trend behind the headline number.

    `?actor=` selects a series (default the platform-wide one); `?limit=` caps
    to the most recent N points. Public and aggregate, consistent with `/cvi`.
    """
    actor = request.args.get("actor", "")
    limit = request.args.get("limit", type=int) if "limit" in request.args else None
    if "limit" in request.args and limit is None:
        return jsonify({"error": "limit must be an integer"}), 400
    return jsonify(cvi_history.list(actor=actor, limit=limit))


@app.route("/badge/cvi.svg", methods=["GET"])
def cvi_badge():
    """The live CVI as an embeddable SVG badge — the trust index for a README.

    Grey `verification` label, coloured value: green at or above the 0.74
    threshold, stepping down to red below it, so a badge pinned to the repo
    reads the same truth the terminal does. Public and aggregate like `/cvi`;
    `?label=` overrides the left cell. Sent no-cache so an embed shows the
    current index, not a stale one.
    """
    value = attestation_engine.cvi(released_ids=held_review_log.released_ids())["cvi"]
    label = request.args.get("label", "verification")
    svg = badge.render(label, f"{value:.2f}", badge.cvi_color(value))
    resp = Response(svg, mimetype=badge.CONTENT_TYPE)
    resp.headers["Cache-Control"] = "no-cache, max-age=0"
    return resp


def _status_snapshot() -> dict[str, Any]:
    """Assemble the live trust posture once, for both `/status` and `/status.json`.

    A single source so the human page and the machine twin can never disagree.
    Reduces the record to a single `posture` verdict — `TRUSTWORTHY` (chain
    intact, sealed head reproduced and signed), `INTACT` (intact but not yet
    sealed), or `BROKEN` (with the broken-at id) — plus the underlying signals.
    """
    verify = attestation_engine.verify()
    released = held_review_log.released_ids()
    cvi = attestation_engine.cvi(released_ids=released)
    held = attestation_engine.held()
    held_pending = [att for att in held if att["id"] not in released]
    held_breached = sum(
        1
        for att in held
        if sla_status(
            att["created_at"], held_review_log.latest_for(att["id"]), HELD_SLA_SECONDS
        ).get("sla_breached")
    )
    if not verify["intact"]:
        posture, posture_class = "BROKEN", "bad"
    elif verify.get("trustworthy"):
        posture, posture_class = "TRUSTWORTHY", "ok"
    else:
        posture, posture_class = "INTACT", "warn"
    return {
        "posture": posture,
        "posture_class": posture_class,
        "verify": verify,
        "cvi": cvi,
        "attestations_total": len(attestation_engine.list()),
        "held_pending": len(held_pending),
        "held_breached": held_breached,
        "builds_total": len(service.list_builds()),
        "users_total": len(auth_registry.list_users()),
        "checkpoint": attestation_engine.latest_checkpoint(),
        "audit": drift_audit_log.latest(),
        "threshold": CONFIDENCE_THRESHOLD,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


@app.route("/status", methods=["GET"])
def status_page():
    """A public, server-rendered trust posture page — the platform's status board.

    Read-only and unauthenticated, distinct from the operator console (`/`): no
    actions, just the live verification posture at a glance — the CVI and its
    spread, chain integrity and its seal, the held queue and its SLA, the last
    checkpoint and the last drift audit. Rendered server-side so it works with no
    JavaScript, and it embeds the CVI badge (`/badge/cvi.svg`). The one page you
    link someone to answer "is the verification layer healthy right now?".
    """
    return render_template("status.html", **_status_snapshot())


@app.route("/status.json", methods=["GET"])
def status_json():
    """The machine-readable twin of `/status` — the whole posture in one call.

    The same `_status_snapshot` the page renders, as JSON, so a monitor or
    dashboard gets the single `posture` verdict and every underlying signal
    without scraping HTML or reassembling it from `/cvi`, `/attestations/verify`,
    and the audit trail separately. `posture_class` (a CSS concern) is dropped.
    """
    snapshot = _status_snapshot()
    snapshot.pop("posture_class", None)
    return jsonify(snapshot)


@app.route("/metrics", methods=["GET"])
def prometheus_metrics():
    """Platform state in the Prometheus text format — scrapeable by any monitor.

    Aggregate scalars only (no per-actor content), consistent with `/cvi` being
    public: verification quality, the held queue and its SLA breaches, and the
    ledger's integrity, all as one standard exposition.
    """
    verify = attestation_engine.verify()
    held = attestation_engine.held()
    released = held_review_log.released_ids()
    held_pending = [att for att in held if att["id"] not in released]
    held_breached = sum(
        1
        for att in held
        if sla_status(
            att["created_at"], held_review_log.latest_for(att["id"]), HELD_SLA_SECONDS
        ).get("sla_breached")
    )
    policy = attestation_engine.checkpoint_policy
    snapshot = [
        {"name": "oceanicos_attestations_total", "help": "Total attestations on record", "value": len(attestation_engine.list())},
        {"name": "oceanicos_attestations_held", "help": "Attestations held below the confidence threshold", "value": len(held)},
        {"name": "oceanicos_held_pending", "help": "Held attestations awaiting a steward decision", "value": len(held_pending)},
        {"name": "oceanicos_held_sla_breached", "help": "Pending held attestations past the review SLA", "value": held_breached},
        {"name": "oceanicos_cvi", "help": "Composite Verification Index (0-1), released items credited", "value": attestation_engine.cvi(released_ids=released)["cvi"]},
        {"name": "oceanicos_builds_total", "help": "Total builds in the ledger", "value": len(service.list_builds())},
        {"name": "oceanicos_users_total", "help": "Registered accounts", "value": len(auth_registry.list_users())},
        {"name": "oceanicos_chain_intact", "help": "Attestation hash chain integrity (1 intact, 0 broken)", "value": bool(verify["intact"])},
        {"name": "oceanicos_chain_length", "help": "Number of links in the attestation chain", "value": verify["length"]},
        {"name": "oceanicos_chain_trustworthy", "help": "Chain intact and signed head verified (1 yes, 0 no)", "value": bool(verify.get("trustworthy"))},
        {"name": "oceanicos_checkpoint_auto", "help": "Automatic checkpoint sealing enabled (1 yes, 0 no)", "value": policy["auto"]},
        {"name": "oceanicos_model_adapters", "help": "Registered dissent-panel adapters", "value": len(model_router.list_adapters())},
        {"name": "oceanicos_last_audit_intact", "help": "Latest drift audit found the chain intact (1 yes/none, 0 broken)", "value": (drift_audit_log.latest() or {}).get("intact", True)},
    ]
    return Response(metrics.render(snapshot), mimetype=metrics.CONTENT_TYPE)


@app.route("/nodes", methods=["POST"])
@require_auth
def mount_node():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    flux = payload.get("flux", "high")
    return jsonify(node_registry.mount(name, flux))


@app.route("/nodes", methods=["GET"])
def list_nodes():
    return jsonify(node_registry.list())


@app.route("/pricing", methods=["GET"])
def pricing():
    return jsonify(
        {
            "service": "Verification-as-a-Service (VaaS)",
            "currency": "USD/month",
            "tiers": [
                {
                    "name": "Attestor",
                    "price": 8500,
                    "includes": [
                        "attestation API",
                        "CVI",
                        "csv/txt ledger exports",
                        "verifiable attestation export",
                    ],
                },
                {
                    "name": "Arbiter",
                    "price": 25500,
                    "includes": ["everything in Attestor", "3-model + rules-engine dissent panels", "held-review SLAs"],
                },
                {
                    "name": "Sovereign",
                    "price": 85000,
                    "includes": [
                        "everything in Arbiter",
                        "on-prem binary distribution",
                        "hardware-key (YubiKey) handoff",
                        "no source escrow",
                    ],
                },
            ],
            "note": "The reference implementation remains open under the charter; commercial delivery is binary + hardware-key handoff.",
        }
    )


@app.route("/observer", methods=["GET"])
def observer():
    constitution = Path(__file__).parent / "CONSTITUTION.md"
    constitution_sha256 = (
        hashlib.sha256(constitution.read_bytes()).hexdigest()
        if constitution.exists()
        else None
    )
    manifest = Path(__file__).parent / "boot" / "init.v1"
    manifest_sha256 = (
        hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.exists() else None
    )
    return jsonify(
        {
            "root": "/",
            "observer": "sole read/write head",
            "stateless": True,
            "sigil": "0xΩ∞v",
            "identity": identity.as_list(),
            "constitution_sha256": constitution_sha256,
            "manifest_sha256": manifest_sha256,
            "anchor_present": anchor.load_anchor()["present"],
            "exit": 0,
            "status": "continues",
        }
    )


@app.route("/anchor", methods=["GET"])
def anchor_of_last_resort():
    """The failover cache surfaced — the 2019 dataset that answers offline.

    An optional ?date=2019-07-04 looks a row up straight from the anchor,
    proving the ground truth is reachable with the rest of the stack ignored.
    """
    state = anchor.load_anchor()
    date = request.args.get("date")
    if date:
        state = {**state, "lookup": {"date": date, "row": anchor.anchor_line(date)}}
    return jsonify(state)


@app.route("/agent/run", methods=["POST"])
def run_agent():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    context = payload.get("context")
    return jsonify(agent_loop.run(task, context))


@app.route("/agent/events", methods=["GET"])
def agent_events():
    return jsonify(agent_loop.events())


@app.route("/state", methods=["POST"])
def record_state():
    payload = request.get_json(silent=True) or {}
    event = payload.get("event", "")
    detail = payload.get("detail")
    state_snapshot.record(event, detail)
    return jsonify(state_snapshot.snapshot())


@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state_snapshot.snapshot())


@app.route("/reviews", methods=["POST"])
def submit_review():
    payload = request.get_json(silent=True) or {}
    proposal = payload.get("proposal", "")
    reviewer = payload.get("reviewer", "")
    return jsonify(review_engine.submit(proposal, reviewer))


@app.route("/reviews/<proposal>/approve", methods=["POST"])
def approve_review(proposal: str):
    return jsonify(review_engine.approve(proposal))


@app.route("/reviews", methods=["GET"])
def list_reviews():
    return jsonify(review_engine.list_reviews())


@app.route("/decisions", methods=["POST"])
def record_decision():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    context = payload.get("context", "")
    decision = payload.get("decision", "")
    return jsonify(decision_registry.record(title, context, decision))


@app.route("/decisions", methods=["GET"])
def list_decisions():
    return jsonify(decision_registry.list())


@app.route("/adr", methods=["GET"])
def list_architecture_decisions():
    """The Architecture Decision Records — why the platform is the way it is."""
    return jsonify(adr.list_adr())


@app.route("/adr/<int:number>", methods=["GET"])
def get_architecture_decision(number: int):
    """One ADR with its full text; 404 if there is no such record."""
    record = adr.get_adr(number)
    if record is None:
        return jsonify({"error": f"no ADR #{number}"}), 404
    return jsonify(record)


@app.route("/artifacts", methods=["POST"])
def create_artifact():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    kind = payload.get("kind", "")
    status = payload.get("status", "draft")
    return jsonify(artifact_registry.create(name, kind, status))


@app.route("/artifacts", methods=["GET"])
def list_artifacts():
    return jsonify(artifact_registry.list())


@app.route("/dashboard", methods=["POST"])
def add_dashboard_item():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    kind = payload.get("kind", "")
    status = payload.get("status", "active")
    dashboard.add(title, kind, status)
    return jsonify(dashboard.summary())


@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    return jsonify(dashboard.summary())


@app.route("/builder/run", methods=["POST"])
@require_auth
def run_builder():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "Draft a charter update")
    context = payload.get("context", "Open orchestration")

    # Named actors are metered against their tier; the open anonymous path is not.
    if g.actor != ANONYMOUS:
        status = _windowed_quota(g.actor, g.tier)
        if status["exceeded"]:
            usage_log.record(g.actor, "quota_exceeded", g.tier, task)
            resp = jsonify(
                {
                    "error": "quota exceeded",
                    "tier": status["tier"],
                    "limit": status["limit"],
                    "used": status["used"],
                    "window_seconds": status["window_seconds"],
                    "resets_at": status["resets_at"],
                }
            )
            resp.headers.extend(_rate_limit_headers(status))
            return resp, 429

    result = builder.run(task, context, actor=g.actor)
    usage_log.record(g.actor, "build", g.tier, task)
    _snapshot_cvi(g.actor)  # platform + this actor's trend
    result["dashboard"] = dashboard.summary()
    resp = jsonify(result)
    if g.actor != ANONYMOUS:
        # recompute after the build so Remaining reflects the slot just consumed
        resp.headers.extend(_rate_limit_headers(_windowed_quota(g.actor, g.tier)))
    return resp


@app.route("/builder/history", methods=["GET"])
def builder_history():
    return jsonify(builder.history())


@app.route("/builder/evolve", methods=["POST", "GET"])
@require_auth
def builder_evolve():
    return jsonify(builder.evolve())


@app.route("/auth/register", methods=["POST"])
def auth_register():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    return jsonify(auth_registry.register(username))


@app.route("/auth/whoami", methods=["GET"])
def auth_whoami():
    user = _current_user()
    return jsonify(
        {"actor": user["username"], "role": user["role"], "tier": user["tier"]}
    )


@app.route("/auth/users", methods=["GET"])
def auth_users():
    return jsonify(auth_registry.list_users())


@app.route("/admin/users/<username>/tier", methods=["POST"])
@require_admin
def admin_set_tier(username: str):
    payload = request.get_json(silent=True) or {}
    tier = payload.get("tier", "")
    result = auth_registry.set_tier(username, tier)
    usage_log.record(username, "tier_change", tier, f"by {g.actor}")
    return jsonify(result)


@app.route("/admin/usage", methods=["GET"])
@require_admin
def admin_usage():
    actor = request.args.get("actor")
    return jsonify(usage_log.list(actor=actor))


@app.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    users = auth_registry.list_users(include_role=True)
    builds = service.list_builds()
    counts: dict[str, int] = {}
    for build in builds:
        counts[build["actor"]] = counts.get(build["actor"], 0) + 1
    for user in users:
        user["builds"] = counts.get(user["username"], 0)
    return jsonify(users)


@app.route("/admin/overview", methods=["GET"])
@require_admin
def admin_overview():
    builds = service.list_builds()
    attestations = attestation_engine.list()
    held = attestation_engine.held()
    released = held_review_log.released_ids()
    held_pending = len([att for att in held if att["id"] not in released])
    held_sla_breached = sum(
        1
        for att in held
        if sla_status(
            att["created_at"], held_review_log.latest_for(att["id"]), HELD_SLA_SECONDS
        ).get("sla_breached")
    )
    return jsonify(
        {
            "users": len(auth_registry.list_users()),
            "builds": len(builds),
            "attestations": len(attestations),
            "held": len(held),
            "held_pending": held_pending,
            "held_sla_breached": held_sla_breached,
            "held_sla_seconds": HELD_SLA_SECONDS,
            "cvi": attestation_engine.cvi(released_ids=released)["cvi"],
            "chain": attestation_engine.verify(),
            "checkpoint_policy": attestation_engine.checkpoint_policy,
            "actors": sorted({build["actor"] for build in builds}),
            "usage": usage_log.summary()["by_action"],
        }
    )


def _effective_config() -> dict:
    """The configuration this process is actually running — from live objects.

    Read from the live components, not raw env, so it reports the truth the
    process is running, not the intent someone set. Contains no secret value:
    signing is reported as the boolean `signing_enabled` (the key never leaves
    the engine), and no token is ever assembled here.
    """
    return {
        "require_auth": bool(app.config.get("REQUIRE_AUTH")),
        "signing_enabled": attestation_engine.can_sign,
        "checkpoint": attestation_engine.checkpoint_policy,
        "quota": {
            "window_seconds": quotas.WINDOW_SECONDS,
            "tier_limits": dict(quotas.TIER_LIMITS),
        },
        "held_sla_seconds": HELD_SLA_SECONDS,
        "admins": len(auth_registry.admin_users),
        "model_adapters": [a["name"] for a in model_router.list_adapters()],
        "db_path": str(service.db_path),
        "workspace": os.getenv("OCEANICOS_WORKSPACE", "workspace"),
        "version": "1.0",
    }


def _config_warnings(cfg: dict) -> list[dict]:
    """Flag risky or degraded configurations so misconfig doesn't fail silently.

    Pure function over the effective config: each finding is a `{level, message}`
    (`warn` for a gap that undermines a feature the operator seems to want,
    `info` for a deliberate-but-notable posture). It reports the shape of the
    running config, not the secrets in it.
    """
    findings: list[dict] = []
    if cfg["signing_enabled"] and not cfg["checkpoint"]["auto"]:
        findings.append({
            "level": "warn",
            "message": "signing key set but auto-checkpointing off — the head is "
            "sealed only on a manual POST; set OCEANICOS_CHECKPOINT_EVERY",
        })
    if not cfg["signing_enabled"]:
        findings.append({
            "level": "info",
            "message": "no signing key — the ledger is tamper-evident but not "
            "tamper-resistant (checkpoints unavailable)",
        })
    if cfg["admins"] == 0:
        findings.append({
            "level": "warn",
            "message": "no admin users — held attestations cannot be reviewed; "
            "set OCEANICOS_ADMIN_USERS",
        })
    if not cfg["require_auth"]:
        findings.append({
            "level": "info",
            "message": "auth enforcement off — the open path is unmetered",
        })
    if cfg["held_sla_seconds"] == 0:
        findings.append({"level": "info", "message": "held-review SLA disabled"})
    return findings


@app.route("/config", methods=["GET"])
@require_admin
def effective_config():
    """The effective runtime configuration — what this instance is actually running.

    Stewardship introspection: reports the operational config from the live
    objects (auth mode, quota window and tiers, held SLA, checkpoint policy,
    whether signing is enabled) plus warnings for risky setups — never a secret.
    """
    cfg = _effective_config()
    cfg["warnings"] = _config_warnings(cfg)
    return jsonify(cfg)


@app.route("/me/builds", methods=["GET"])
@require_auth
def my_builds():
    return jsonify(service.list_builds(actor=g.actor))


@app.route("/me/attestations", methods=["GET"])
@require_auth
def my_attestations():
    return jsonify(attestation_engine.list(actor=g.actor))


@app.route("/me/memory", methods=["GET"])
@require_auth
def my_memory():
    query = request.args.get("query", "")
    return jsonify(service.search_memory(query, actor=g.actor))


@app.route("/me/cvi", methods=["GET"])
@require_auth
def my_cvi():
    return jsonify(
        attestation_engine.cvi(
            actor=g.actor, released_ids=held_review_log.released_ids()
        )
    )


@app.route("/me/cvi/history", methods=["GET"])
@require_auth
def my_cvi_history():
    """The authenticated actor's own CVI trend over time."""
    limit = request.args.get("limit", type=int) if "limit" in request.args else None
    if "limit" in request.args and limit is None:
        return jsonify({"error": "limit must be an integer"}), 400
    return jsonify(cvi_history.list(actor=g.actor, limit=limit))


@app.route("/me/quota", methods=["GET"])
@require_auth
def my_quota():
    status = _windowed_quota(g.actor, g.tier)
    resp = jsonify(status)
    resp.headers.extend(_rate_limit_headers(status))
    return resp


@app.route("/me/usage", methods=["GET"])
@require_auth
def my_usage():
    return jsonify(usage_log.list(actor=g.actor))


@app.route("/plugins", methods=["POST"])
def register_plugin():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    capabilities = payload.get("capabilities", [])
    return jsonify(plugin_registry.register(name, capabilities))


@app.route("/plugins", methods=["GET"])
def list_plugins():
    return jsonify(plugin_registry.list())


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
