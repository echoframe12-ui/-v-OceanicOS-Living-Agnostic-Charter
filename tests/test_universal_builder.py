import unittest

from universal_builder import UniversalBuilder


class UniversalBuilderTests(unittest.TestCase):
    def test_run_returns_plan_and_state(self):
        builder = UniversalBuilder()
        result = builder.run("Build the charter platform", "Open orchestration")
        self.assertEqual(result["task"], "Build the charter platform")
        self.assertIn("plan", result)
        self.assertIn("state", result)


if __name__ == "__main__":
    unittest.main()
