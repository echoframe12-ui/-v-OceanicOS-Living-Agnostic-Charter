import unittest

import quotas


class QuotaTests(unittest.TestCase):
    def test_limit_for_known_and_unknown_tiers(self):
        self.assertEqual(quotas.limit_for("attestor"), 10)
        self.assertEqual(quotas.limit_for("arbiter"), 50)
        self.assertIsNone(quotas.limit_for("sovereign"))
        # unknown tier falls back to the default tier's limit
        self.assertEqual(quotas.limit_for("mystery"), quotas.limit_for(quotas.DEFAULT_TIER))

    def test_quota_status_under_at_and_over(self):
        under = quotas.quota_status("attestor", 3)
        self.assertEqual(under["remaining"], 7)
        self.assertFalse(under["exceeded"])

        at = quotas.quota_status("attestor", 10)
        self.assertEqual(at["remaining"], 0)
        self.assertTrue(at["exceeded"])

        over = quotas.quota_status("attestor", 12)
        self.assertEqual(over["remaining"], 0)
        self.assertTrue(over["exceeded"])

    def test_sovereign_is_unlimited(self):
        status = quotas.quota_status("sovereign", 9999)
        self.assertIsNone(status["limit"])
        self.assertIsNone(status["remaining"])
        self.assertFalse(status["exceeded"])

    def test_is_tier(self):
        self.assertTrue(quotas.is_tier("attestor"))
        self.assertFalse(quotas.is_tier("platinum"))

    def test_quota_status_carries_window_fields(self):
        scoped = quotas.quota_status(
            "attestor", 3, window_seconds=3600, resets_at="2026-01-01T00:00:00+00:00"
        )
        self.assertEqual(scoped["window_seconds"], 3600)
        self.assertEqual(scoped["resets_at"], "2026-01-01T00:00:00+00:00")

        bare = quotas.quota_status("attestor", 3)
        self.assertIsNone(bare["window_seconds"])
        self.assertIsNone(bare["resets_at"])


if __name__ == "__main__":
    unittest.main()
