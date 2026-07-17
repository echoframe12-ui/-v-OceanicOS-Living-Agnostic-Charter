import tempfile
import unittest

from universal_builder import UniversalBuilder


def make_builder():
    return UniversalBuilder(workspace_root=tempfile.mkdtemp(prefix="oceanicos-ws-"))


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
                "memory",
                "ledger",
            ],
        )
        self.assertEqual(result["review"]["status"], "approved")
        self.assertEqual(result["artifact"]["status"], "complete")
        self.assertTrue(result["workflow"]["executed"])

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

        builder.run("Build the charter platform")
        report = builder.evolve()
        self.assertEqual(report["runs"], 1)
        self.assertEqual(report["artifacts"], 1)
        self.assertEqual(report["reviews"]["pending"], 0)
        self.assertGreaterEqual(report["persisted_builds"], 1)
        self.assertTrue(report["next_steps"])


if __name__ == "__main__":
    unittest.main()
