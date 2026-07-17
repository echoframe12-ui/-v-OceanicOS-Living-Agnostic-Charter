import os

from flask import Flask, jsonify, render_template, request

from agent import AgentLoop
from artifacts import ArtifactRegistry
from dashboard import Dashboard
from decisions import DecisionRegistry
from models import ModelAdapter, ModelRouter
from planner import Planner
from plugins import PluginRegistry
from review import ReviewEngine
from server import OceanicOSService
from state import StateSnapshot
from workflows import WorkflowEngine

app = Flask(__name__)
service = OceanicOSService()
workflow_engine = WorkflowEngine()
planner = Planner()
model_router = ModelRouter()
model_router.register(ModelAdapter("local", "demo"))
agent_loop = AgentLoop()
state_snapshot = StateSnapshot()
review_engine = ReviewEngine()
decision_registry = DecisionRegistry()
artifact_registry = ArtifactRegistry()
dashboard = Dashboard()
plugin_registry = PluginRegistry()


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
def store_memory():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.store_memory(payload))


@app.route("/memory", methods=["GET"])
def search_memory():
    query = request.args.get("query", "")
    return jsonify(service.search_memory(query))


@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify(service.list_tools())


@app.route("/tools/<name>", methods=["POST"])
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


@app.route("/models/route", methods=["POST"])
def route_model():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    return jsonify(model_router.route(prompt))


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
def run_builder():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "Draft a charter update")
    context = payload.get("context", "Open orchestration")

    plan_result = planner.plan(task, context)
    model_result = model_router.route(task)
    review_result = review_engine.submit(f"Review plan for {task}", "builder")
    decision_result = decision_registry.record(
        f"Run {task}",
        context,
        f"Accepted a builder run for {task}",
    )
    artifact_result = artifact_registry.create(
        task.lower().replace(" ", "-"),
        "plan",
        "draft",
    )

    return jsonify(
        {
            "task": task,
            "plan": plan_result,
            "model": model_result,
            "state": state_snapshot.snapshot(),
            "review": review_result,
            "decision": decision_result,
            "artifact": artifact_result,
            "dashboard": dashboard.summary(),
        }
    )


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
