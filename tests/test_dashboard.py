import unittest

from dashboard import Dashboard


class DashboardTests(unittest.TestCase):
    def test_summary(self):
        dashboard = Dashboard()
        dashboard.add("Plan charter", "plan")
        summary = dashboard.summary()
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["items"][0]["title"], "Plan charter")


if __name__ == "__main__":
    unittest.main()
