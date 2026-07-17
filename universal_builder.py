from __future__ import annotations

import argparse
import json
from typing import Any

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
    """Full build pipeline: plan, workflow, model routing, agent run, review,
    decision, artifact, dashboard, and persistent memory — with a run history
    and an evolution report that suggests the next stage of growth.

    Components can be injected so the builder shares state with a host
    application (for example the Flask app); any component not provided is
    created with a sensible default.
    """

    def __init__(
        self,
        service: OceanicOSService | None = None,
        planner: Planner | None = None,
        workflow_engine: WorkflowEngine | None = None,
        model_router: ModelRouter | None = None,
        agent_loop: AgentLoop | None = None,
        state_snapshot: StateSnapshot | None = None,
        review_engine: ReviewEngine | None = None,
        decision_registry: DecisionRegistry | None = None,
        artifact_registry: ArtifactRegistry | None = None,
        dashboard: Dashboard | None = None,
        plugin_registry: PluginRegistry | None = None,
    ) -> None:
        self.service = service or OceanicOSService()
        self.planner = planner or Planner()
        self.workflow_engine = workflow_engine or WorkflowEngine()
        if model_router is None:
            model_router = ModelRouter()
            model_router.register(ModelAdapter("local", "demo"))
        self.model_router = model_router
        self.agent_loop = agent_loop or AgentLoop()
        self.state_snapshot = state_snapshot or StateSnapshot()
        self.review_engine = review_engine or ReviewEngine()
        self.decision_registry = decision_registry or DecisionRegistry()
        self.artifact_registry = artifact_registry or ArtifactRegistry()
        self.dashboard = dashboard or Dashboard()
        self.plugin_registry = plugin_registry or PluginRegistry()
        self.plugin_registry.register("builder", ["plan", "execute", "review", "evolve"])
        self._runs: list[dict[str, Any]] = []

    def run(self, task: str, context: str | None = None) -> dict[str, Any]:
        run_id = len(self._runs) + 1
        stages: list[str] = []

        plan = self.planner.plan(task, context)
        self.state_snapshot.record("plan_created", task)
        stages.append("plan")

        workflow_name = f"build-{run_id}"
        workflow_steps = [
            {"name": step["name"], "type": "reason"} for step in plan["steps"]
        ]
        self.workflow_engine.create_workflow(workflow_name, workflow_steps)
        workflow = self.workflow_engine.execute_workflow(workflow_name)
        self.state_snapshot.record("workflow_executed", workflow_name)
        stages.append("workflow")

        model_result = self.model_router.route(task)
        stages.append("route")

        agent_result = self.agent_loop.run(task, context)
        stages.append("agent")

        proposal = f"Build run {run_id}: {task}"
        self.review_engine.submit(proposal, "universal-builder")
        review = self.review_engine.approve(proposal)
        stages.append("review")

        decision = self.decision_registry.record(
            f"Build run {run_id}",
            context or "general",
            f"Executed the full build pipeline for: {task}",
        )
        stages.append("decision")

        artifact = self.artifact_registry.create(
            task.lower().replace(" ", "-"),
            "build",
            "complete",
        )
        self.dashboard.add(task, "build", "complete")
        stages.append("artifact")

        self.service.store_memory(
            {
                "text": f"Build run {run_id}: {task}",
                "source": "universal-builder",
                "context": context or "general",
            }
        )
        self.state_snapshot.record("builder_run_complete", task)
        stages.append("memory")

        result = {
            "run_id": run_id,
            "task": task,
            "context": context or "general",
            "stages": stages,
            "plan": plan,
            "workflow": workflow,
            "model": model_result,
            "agent": {"task": agent_result["task"]},
            "review": review,
            "decision": decision,
            "artifact": artifact,
            "state": self.state_snapshot.snapshot(),
        }
        self._runs.append(
            {
                "run_id": run_id,
                "task": task,
                "context": context or "general",
                "stages": stages,
                "artifact": artifact["name"],
            }
        )
        return result

    def run_many(self, tasks: list[str], context: str | None = None) -> list[dict[str, Any]]:
        return [self.run(task, context) for task in tasks]

    def history(self) -> list[dict[str, Any]]:
        return list(self._runs)

    def evolve(self) -> dict[str, Any]:
        """Summarize what the builder has produced and propose the next stage."""
        reviews = self.review_engine.list_reviews()
        artifacts = self.artifact_registry.list()
        pending_reviews = [r for r in reviews if r["status"] == "pending"]
        draft_artifacts = [a for a in artifacts if a["status"] == "draft"]

        next_steps: list[str] = []
        if not self._runs:
            next_steps.append("Run the builder on a first task to seed the pipeline")
        if pending_reviews:
            next_steps.append(f"Resolve {len(pending_reviews)} pending review(s)")
        if draft_artifacts:
            next_steps.append(f"Promote {len(draft_artifacts)} draft artifact(s)")
        next_steps.append("Connect a real model provider through a new ModelAdapter")
        next_steps.append("Register external tool plugins (GitHub, calendar, files)")
        next_steps.append("Grow the layer directories with working engine implementations")

        return {
            "runs": len(self._runs),
            "artifacts": len(artifacts),
            "decisions": len(self.decision_registry.list()),
            "reviews": {
                "total": len(reviews),
                "pending": len(pending_reviews),
            },
            "plugins": len(self.plugin_registry.list()),
            "next_steps": next_steps,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OceanicOS universal builder")
    parser.add_argument("task", nargs="?", default="Build the charter platform")
    parser.add_argument("--context", default="Open orchestration")
    parser.add_argument(
        "--evolve",
        action="store_true",
        help="Print the evolution report after the run",
    )
    args = parser.parse_args()

    builder = UniversalBuilder()
    result = builder.run(args.task, args.context)
    print(json.dumps(result, indent=2))
    if args.evolve:
        print(json.dumps(builder.evolve(), indent=2))


if __name__ == "__main__":
    main()
