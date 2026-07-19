import tempfile
import unittest

from models import (
    ModelAdapter,
    ModelRouter,
    strategy_literal,
    strategy_optimist,
    strategy_skeptic,
)
from universal_builder import UniversalBuilder


def make_builder():
    return UniversalBuilder(workspace_root=tempfile.mkdtemp(prefix="oceanicos-ws-"))


def panel_router():
    router = ModelRouter()
    router.register(ModelAdapter("local", "demo", strategy=strategy_literal))
    router.register(ModelAdapter("reasoning", "demo", keywords=["plan"], strategy=strategy_optimist))
    router.register(ModelAdapter("skeptic", "demo", keywords=["verify"], strategy=strategy_skeptic))
    return router


def make_panel_builder():
    return UniversalBuilder(
        model_router=panel_router(),
        workspace_root=tempfile.mkdtemp(prefix="oceanicos-ws-"),
    )


class UniversalBuilderTests(unittest.TestCase):
    def test_run_returns_plan_and_state(self):
        builder = make_builder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertEqual(result["task"], "Build the charter platform")
        self.assertIn("plan", result)
        self.assertIn("state", result)

    def test_run_executes_full_pipeline(self):
        builder = make_builder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertEqual(result["run_id"], 1)
        self.assertEqual(
            result["stages"],
            [
                "plan",
                "workflow",
                "route",
                "agent",
                "review",
                "decision",
                "artifact",
                "workspace",
                "attest",
                "memory",
                "ledger",
            ],
        )
        self.assertEqual(result["review"]["status"], "approved")
        self.assertEqual(result["artifact"]["status"], "complete")
        self.assertTrue(result["workflow"]["executed"])
        self.assertEqual(result["attestation"]["status"], "attested")
        self.assertGreaterEqual(result["attestation"]["confidence"], 0.74)
        self.assertEqual(len(result["attestation"]["sha256"]), 64)

    def test_run_without_context_is_held_for_review(self):
        builder = make_builder()
        result = builder.run("Build the charter platform")
        self.assertEqual(result["attestation"]["status"], "held")
        self.assertLess(result["attestation"]["confidence"], 0.74)
        self.assertEqual(result["review"]["status"], "pending")

        report = builder.evolve()
        self.assertEqual(report["attestations"]["held"], 1)
        self.assertTrue(
            any("held attestation" in step for step in report["next_steps"])
        )

    def test_unanimous_revise_holds_even_a_well_evidenced_build(self):
        builder = make_panel_builder()
        # "Draft a thorough governance overhaul" -> literal revise (>4 words),
        # optimist revise (no plan/build/ship/design), skeptic revise (no evidence)
        result = builder.run("Draft a thorough governance overhaul", "full context")
        self.assertFalse(result["consensus"]["dissent"])
        self.assertEqual(result["consensus"]["majority"], "revise")
        self.assertEqual(result["attestation"]["status"], "held")
        self.assertEqual(result["review"]["status"], "pending")

    def test_unanimous_approve_rescues_a_context_free_build(self):
        builder = make_panel_builder()
        # "ship" -> literal approve (<=4 words), optimist approve (ship),
        # skeptic revise (no evidence) ... not unanimous; use an all-approve prompt
        # "plan verified" -> optimist approve (plan), skeptic approve (verified),
        # literal approve (<=4 words) => unanimous approve
        result = builder.run("plan verified", None)
        self.assertEqual(result["consensus"]["majority"], "approve")
        self.assertFalse(result["consensus"]["dissent"])
        self.assertEqual(result["attestation"]["status"], "attested")

    def test_consensus_is_recorded_in_the_attestation_trail(self):
        builder = make_panel_builder()
        result = builder.run("Plan the build", "ctx")
        self.assertTrue(
            any(s.startswith("consensus:") for s in result["attestation"]["sources"])
        )

    def test_run_attributes_actor(self):
        builder = make_builder()
        result = builder.run("Attributed build", "Identity", actor="alice")
        self.assertEqual(result["actor"], "alice")
        self.assertIn("actor:alice", result["attestation"]["sources"])

        builds = builder.service.list_builds()
        self.assertEqual(builds[-1]["actor"], "alice")

    def test_run_defaults_to_anonymous_actor(self):
        builder = make_builder()
        result = builder.run("Unattributed build", "Identity")
        self.assertEqual(result["actor"], "anonymous")

    def test_run_writes_build_file_to_workspace(self):
        builder = make_builder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertTrue(result["build_file"]["written"])
        self.assertEqual(
            result["build_file"]["path"], "builds/build-the-charter-platform.md"
        )
        content = builder.service.invoke_tool(
            "file_read", {"path": result["build_file"]["path"]}
        )
        self.assertIn("Build run 1: Build the charter platform", content["content"])

    def test_history_tracks_runs(self):
        builder = make_builder()
        builder.run_many(["First task", "Second task"], "Testing")
        history = builder.history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["run_id"], 1)
        self.assertEqual(history[1]["task"], "Second task")

    def test_evolve_reports_progress_and_next_steps(self):
        builder = make_builder()
        report = builder.evolve()
        self.assertEqual(report["runs"], 0)
        self.assertIn("Run the builder on a first task to seed the pipeline", report["next_steps"])

        builder.run("Build the charter platform", "Open orchestration")
        report = builder.evolve()
        self.assertEqual(report["runs"], 1)
        self.assertEqual(report["artifacts"], 1)
        self.assertEqual(report["reviews"]["pending"], 0)
        self.assertEqual(report["attestations"]["held"], 0)
        self.assertGreaterEqual(report["persisted_builds"], 1)
        self.assertTrue(report["next_steps"])
        self.assertIn(
            "Add authentication and multi-user support to the platform",
            report["next_steps"],
        )


if __name__ == "__main__":
    unittest.main()
