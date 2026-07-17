import unittest

from state import StateSnapshot


class StateSnapshotTests(unittest.TestCase):
    def test_record_and_snapshot(self):
        snapshot = StateSnapshot()
        snapshot.record("start", "agent initialized")
        snapshot.record("finish", "task completed")
        state = snapshot.snapshot()
        self.assertEqual(state["count"], 2)
        self.assertEqual(state["events"][0]["event"], "start")


if __name__ == "__main__":
    unittest.main()
