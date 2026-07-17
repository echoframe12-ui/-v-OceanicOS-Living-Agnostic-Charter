import unittest

from universal_builder import UniversalBuilder


class UniversalBuilderTests(unittest.TestCase):
    def test_run_returns_plan_and_state(self):
        builder = UniversalBuilder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertEqual(result["task"], "Build the charter platform")
        self.assertIn("plan", result)
        self.assertIn("state", result)

    def test_run_executes_full_pipeline(self):
        builder = UniversalBuilder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertEqual(result["run_id"], 1)
        self.assertEqual(
            result["stages"],
            ["plan", "workflow", "route", "agent", "review", "decision", "artifact", "memory"],
        )
        self.assertEqual(result["review"]["status"], "approved")
        self.assertEqual(result["artifact"]["status"], "complete")
        self.assertTrue(result["workflow"]["executed"])

    def test_history_tracks_runs(self):
        builder = UniversalBuilder()
        builder.run_many(["First task", "Second task"], "Testing")
        history = builder.history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["run_id"], 1)
        self.assertEqual(history[1]["task"], "Second task")

    def test_evolve_reports_progress_and_next_steps(self):
        builder = UniversalBuilder()
        report = builder.evolve()
        self.assertEqual(report["runs"], 0)
        self.assertIn("Run the builder on a first task to seed the pipeline", report["next_steps"])

        builder.run("Build the charter platform")
        report = builder.evolve()
        self.assertEqual(report["runs"], 1)
        self.assertEqual(report["artifacts"], 1)
        self.assertEqual(report["reviews"]["pending"], 0)
        self.assertTrue(report["next_steps"])


if __name__ == "__main__":
    unittest.main()
