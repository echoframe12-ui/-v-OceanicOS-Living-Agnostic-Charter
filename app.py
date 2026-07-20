import csv
import hashlib
import io
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, Response, g, jsonify, render_template, request

from agent import AgentLoop
from artifacts import ArtifactRegistry
from attestation import AttestationEngine
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
from usage import UsageLog
from review import ReviewEngine
from server import OceanicOSService
from state import StateSnapshot
from universal_builder import UniversalBuilder
from workflows import WorkflowEngine

app = Flask(__name__)
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
agent_loop = AgentLoop()
state_snapshot = StateSnapshot()
review_engine = ReviewEngine()
decision_registry = DecisionRegistry()
artifact_registry = ArtifactRegistry()
dashboard = Dashboard()
plugin_registry = PluginRegistry()
attestation_engine = AttestationEngine(
    str(service.db_path), signing_key=os.getenv("OCEANICOS_SIGNING_KEY", "")
)
node_registry = NodeRegistry()
auth_registry = AuthRegistry()
usage_log = UsageLog(str(service.db_path))
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
    return jsonify(model_router.route_all(prompt, panel=3))


@app.route("/attestations", methods=["GET"])
def list_attestations():
    actor = request.args.get("actor")
    return jsonify(attestation_engine.list(actor=actor))


@app.route("/attestations/verify", methods=["GET"])
def verify_attestations():
    """Confirm the ledger has not been tampered with.

    Walks the hash chain (edit-in-place detection) and checks the latest signed
    checkpoint (whole-rewrite detection): a record is trustworthy only when the
    chain is intact, its signed head is still reproduced, and the signature
    validates under the current key.
    """
    return jsonify(attestation_engine.verify())


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
        return jsonify(attestation_engine.checkpoint())
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409


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
    return jsonify(attestation_engine.cvi())


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
                    "includes": ["everything in Attestor", "3-adapter dissent panels", "held-review SLAs"],
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
    return jsonify(
        {
            "root": "/",
            "observer": "sole read/write head",
            "stateless": True,
            "sigil": "0xΩ∞v",
            "constitution_sha256": constitution_sha256,
            "exit": 0,
            "status": "continues",
        }
    )


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
            return (
                jsonify(
                    {
                        "error": "quota exceeded",
                        "tier": status["tier"],
                        "limit": status["limit"],
                        "used": status["used"],
                        "window_seconds": status["window_seconds"],
                        "resets_at": status["resets_at"],
                    }
                ),
                429,
            )

    result = builder.run(task, context, actor=g.actor)
    usage_log.record(g.actor, "build", g.tier, task)
    result["dashboard"] = dashboard.summary()
    return jsonify(result)


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
    return jsonify(
        {
            "users": len(auth_registry.list_users()),
            "builds": len(builds),
            "attestations": len(attestations),
            "held": len(attestation_engine.held()),
            "cvi": attestation_engine.cvi()["cvi"],
            "chain": attestation_engine.verify(),
            "actors": sorted({build["actor"] for build in builds}),
            "usage": usage_log.summary()["by_action"],
        }
    )


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
    return jsonify(attestation_engine.cvi(actor=g.actor))


@app.route("/me/quota", methods=["GET"])
@require_auth
def my_quota():
    return jsonify(_windowed_quota(g.actor, g.tier))


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
