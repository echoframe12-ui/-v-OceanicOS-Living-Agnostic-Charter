from __future__ import annotations

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


class UniversalBuilder:
    def __init__(self) -> None:
        self.service = OceanicOSService()
        self.planner = Planner()
        self.workflow_engine = WorkflowEngine()
        self.model_router = ModelRouter()
        self.model_router.register(ModelAdapter("local", "demo"))
        self.agent_loop = AgentLoop()
        self.state_snapshot = StateSnapshot()
        self.review_engine = ReviewEngine()
        self.decision_registry = DecisionRegistry()
        self.artifact_registry = ArtifactRegistry()
        self.dashboard = Dashboard()
        self.plugin_registry = PluginRegistry()

    def run(self, task: str, context: str | None = None) -> dict[str, object]:
        plan = self.planner.plan(task, context)
        self.state_snapshot.record("plan_created", task)
        self.workflow_engine.create_workflow("main", [{"name": "plan", "type": "reason"}])
        self.review_engine.submit(task, "builder")
        self.decision_registry.record("Build plan", context or "general", task)
        self.artifact_registry.create(task, "plan")
        self.dashboard.add(task, "plan", "active")
        self.plugin_registry.register("builder", ["plan", "execute"])
        self.agent_loop.run(task, context)
        model_result = self.model_router.route(task)
        return {
            "task": task,
            "plan": plan,
            "model": model_result,
            "state": self.state_snapshot.snapshot(),
        }


if __name__ == "__main__":
    builder = UniversalBuilder()
    result = builder.run("Build the charter platform", "Open orchestration")
    print(result)
