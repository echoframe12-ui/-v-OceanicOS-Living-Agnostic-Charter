import unittest

from planner import Planner


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.planner = Planner()

    def test_plan_records_trace(self):
        result = self.planner.plan("Draft the charter", "This is a governance update")
        self.assertEqual(result["task"], "Draft the charter")
        self.assertEqual(len(result["steps"]), 4)
        self.assertEqual(len(self.planner.get_trace()), 1)


if __name__ == "__main__":
    unittest.main()
