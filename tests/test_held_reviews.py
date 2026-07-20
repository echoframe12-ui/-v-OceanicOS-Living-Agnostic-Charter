import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from held_reviews import RELEASE, UPHOLD, HeldReviewLog, sla_status


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


class SlaStatusTests(unittest.TestCase):
    def setUp(self):
        self.held_at = datetime(2019, 7, 4, 12, 0, 0, tzinfo=timezone.utc)
        self.held_iso = self.held_at.isoformat()

    def test_pending_within_sla_is_not_breached(self):
        now = self.held_at + timedelta(seconds=100)
        status = sla_status(self.held_iso, None, sla_seconds=3600, now=now)
        self.assertEqual(status["state"], "pending")
        self.assertEqual(status["age_seconds"], 100)
        self.assertFalse(status["sla_breached"])

    def test_pending_past_sla_is_breached(self):
        now = self.held_at + timedelta(seconds=7200)
        status = sla_status(self.held_iso, None, sla_seconds=3600, now=now)
        self.assertTrue(status["sla_breached"])

    def test_sla_of_zero_never_breaches(self):
        now = self.held_at + timedelta(days=365)
        status = sla_status(self.held_iso, None, sla_seconds=0, now=now)
        self.assertFalse(status["sla_breached"])

    def test_decided_within_sla(self):
        review = {"verdict": RELEASE, "created_at": (self.held_at + timedelta(seconds=600)).isoformat()}
        status = sla_status(self.held_iso, review, sla_seconds=3600)
        self.assertEqual(status["state"], "decided")
        self.assertEqual(status["verdict"], RELEASE)
        self.assertEqual(status["decision_seconds"], 600)
        self.assertTrue(status["within_sla"])

    def test_decided_past_sla_is_not_within(self):
        review = {"verdict": UPHOLD, "created_at": (self.held_at + timedelta(seconds=9000)).isoformat()}
        status = sla_status(self.held_iso, review, sla_seconds=3600)
        self.assertFalse(status["within_sla"])


if __name__ == "__main__":
    unittest.main()
