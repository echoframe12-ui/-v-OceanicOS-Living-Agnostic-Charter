import unittest

from decisions import DecisionRegistry


class DecisionRegistryTests(unittest.TestCase):
    def test_record_and_list(self):
        registry = DecisionRegistry()
        registry.record("Use SQLite", "Need simple persistence", "Store memory in SQLite")
        decisions = registry.list()
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["title"], "Use SQLite")


if __name__ == "__main__":
    unittest.main()
