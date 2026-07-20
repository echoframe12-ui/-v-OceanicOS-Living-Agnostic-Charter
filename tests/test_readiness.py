import os
import tempfile
import unittest

import readiness


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.workspace = tempfile.mkdtemp(prefix="oceanicos-ready-")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_db_check_passes_for_a_real_database(self):
        self.assertTrue(readiness.check_db(self.db_path))

    def test_db_check_fails_for_an_unusable_path(self):
        # a directory is not a valid sqlite database file
        self.assertFalse(readiness.check_db(self.workspace))

    def test_workspace_check_passes_for_a_writable_dir(self):
        self.assertTrue(readiness.check_workspace(self.workspace))

    def test_workspace_check_creates_a_missing_dir(self):
        nested = os.path.join(self.workspace, "made", "on", "demand")
        self.assertTrue(readiness.check_workspace(nested))
        self.assertTrue(os.path.isdir(nested))

    def test_probe_is_ready_when_all_checks_pass(self):
        report = readiness.probe(self.db_path, self.workspace)
        self.assertTrue(report["ready"])
        self.assertEqual(report["checks"], {"db": True, "workspace": True})

    def test_probe_is_not_ready_when_a_dependency_fails(self):
        report = readiness.probe(self.workspace, self.workspace)  # bad db path
        self.assertFalse(report["ready"])
        self.assertFalse(report["checks"]["db"])


if __name__ == "__main__":
    unittest.main()
