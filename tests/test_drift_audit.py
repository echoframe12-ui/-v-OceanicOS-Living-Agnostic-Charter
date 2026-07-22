import os
import tempfile
import unittest

from drift_audit import DriftAuditLog


class DriftAuditLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = DriftAuditLog(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_records_an_intact_report(self):
        entry = self.log.record({"intact": True, "trustworthy": True, "length": 3, "broken_at": None})
        self.assertEqual(entry["id"], 1)
        self.assertTrue(entry["intact"])
        self.assertTrue(entry["trustworthy"])
        self.assertEqual(entry["length"], 3)

    def test_records_a_broken_report(self):
        entry = self.log.record({"intact": False, "length": 5, "broken_at": 2})
        self.assertFalse(entry["intact"])
        self.assertFalse(entry["trustworthy"])  # absent -> false
        self.assertEqual(entry["broken_at"], 2)

    def test_list_is_newest_first_with_limit(self):
        for i in range(3):
            self.log.record({"intact": True, "length": i})
        history = self.log.list()
        self.assertEqual([h["length"] for h in history], [2, 1, 0])  # newest first
        self.assertEqual(len(self.log.list(limit=2)), 2)

    def test_latest_returns_the_most_recent(self):
        self.assertIsNone(self.log.latest())
        self.log.record({"intact": True, "length": 1})
        self.log.record({"intact": False, "length": 1, "broken_at": 1})
        self.assertFalse(self.log.latest()["intact"])


if __name__ == "__main__":
    unittest.main()
