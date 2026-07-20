import os
import tempfile
import unittest

from cvi_history import CviHistory


def snap(cvi, samples, mean=0.8, held=0.0):
    return {"cvi": cvi, "mean_confidence": mean, "held_ratio": held, "samples": samples}


class CviHistoryTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.history = CviHistory(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_and_list_oldest_first(self):
        self.history.record(snap(0.5, 1))
        self.history.record(snap(0.7, 2))
        series = self.history.list()
        self.assertEqual([p["cvi"] for p in series], [0.5, 0.7])

    def test_limit_returns_most_recent_in_order(self):
        for i in range(5):
            self.history.record(snap(0.1 * i, i))
        recent = self.history.list(limit=2)
        self.assertEqual([p["samples"] for p in recent], [3, 4])

    def test_record_if_changed_skips_identical(self):
        self.assertIsNotNone(self.history.record_if_changed(snap(0.5, 1)))
        self.assertIsNone(self.history.record_if_changed(snap(0.5, 1)))  # unchanged
        self.assertIsNotNone(self.history.record_if_changed(snap(0.6, 2)))  # moved
        self.assertEqual(len(self.history.list()), 2)

    def test_series_are_scoped_by_actor(self):
        self.history.record(snap(0.9, 1), actor="alice")
        self.history.record(snap(0.4, 1), actor="bob")
        self.assertEqual(len(self.history.list(actor="alice")), 1)
        self.assertEqual(self.history.list(actor="alice")[0]["cvi"], 0.9)
        self.assertEqual(self.history.list()[:], [])  # platform series empty


if __name__ == "__main__":
    unittest.main()
