import os
import tempfile
import unittest

from held_reviews import RELEASE, UPHOLD, HeldReviewLog


class HeldReviewLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = HeldReviewLog(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_and_list(self):
        entry = self.log.record(7, "steward", RELEASE, "evidence checked out")
        self.assertEqual(entry["id"], 1)
        self.assertEqual(entry["attestation_id"], 7)
        self.assertEqual(len(self.log.list()), 1)
        self.assertEqual(len(self.log.list(attestation_id=7)), 1)
        self.assertEqual(self.log.list(attestation_id=99), [])

    def test_latest_for_returns_the_most_recent(self):
        self.log.record(3, "a", UPHOLD, "not yet")
        self.log.record(3, "b", RELEASE, "now ok")
        self.assertEqual(self.log.latest_for(3)["verdict"], RELEASE)
        self.assertIsNone(self.log.latest_for(404))

    def test_released_ids_honors_latest_wins(self):
        # uphold then release -> released
        self.log.record(1, "s", UPHOLD, "hold")
        self.log.record(1, "s", RELEASE, "release")
        # release then uphold -> not released (re-held)
        self.log.record(2, "s", RELEASE, "release")
        self.log.record(2, "s", UPHOLD, "changed my mind")
        # single release
        self.log.record(3, "s", RELEASE, "clean")
        self.assertEqual(self.log.released_ids(), {1, 3})


if __name__ == "__main__":
    unittest.main()
