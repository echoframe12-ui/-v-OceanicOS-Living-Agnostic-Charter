import os
import tempfile
import unittest

from supersession import SupersessionLog


class SupersessionLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = SupersessionLog(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_and_lineage(self):
        self.log.record(1, 2, "alice", "re-verified the revised charter")
        # #1 is superseded by #2; #2 supersedes #1
        old = self.log.lineage(1)
        self.assertEqual(old["superseded_by"], [2])
        self.assertFalse(old["is_current"])
        new = self.log.lineage(2)
        self.assertEqual(new["supersedes"], [1])
        self.assertTrue(new["is_current"])

    def test_chain_of_versions(self):
        self.log.record(1, 2, "a", "v2")
        self.log.record(2, 3, "a", "v3")
        # #2 both supersedes #1 and is superseded by #3 -> not current
        mid = self.log.lineage(2)
        self.assertEqual(mid["supersedes"], [1])
        self.assertEqual(mid["superseded_by"], [3])
        self.assertFalse(mid["is_current"])
        # #3 is the current version
        self.assertTrue(self.log.lineage(3)["is_current"])

    def test_exists_guard(self):
        self.assertFalse(self.log.exists(1, 2))
        self.log.record(1, 2, "a", "r")
        self.assertTrue(self.log.exists(1, 2))

    def test_unlinked_attestation_is_current(self):
        line = self.log.lineage(99)
        self.assertEqual(line["supersedes"], [])
        self.assertEqual(line["superseded_by"], [])
        self.assertTrue(line["is_current"])


if __name__ == "__main__":
    unittest.main()
