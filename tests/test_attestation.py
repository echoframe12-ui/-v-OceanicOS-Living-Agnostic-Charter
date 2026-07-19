import hashlib
import unittest

from attestation import CONFIDENCE_THRESHOLD, AttestationEngine, score_confidence


class ScoreConfidenceTests(unittest.TestCase):
    def test_more_evidence_means_more_confidence(self):
        low = score_confidence(["plan"], True)
        high = score_confidence(["plan", "workflow", "route", "agent"], True)
        self.assertGreater(high, low)

    def test_missing_context_drops_below_threshold(self):
        stages = ["plan", "workflow", "route", "agent", "review", "decision", "artifact", "workspace"]
        with_context = score_confidence(stages, True)
        without_context = score_confidence(stages, False)
        self.assertGreaterEqual(with_context, CONFIDENCE_THRESHOLD)
        self.assertLess(without_context, CONFIDENCE_THRESHOLD)

    def test_confidence_is_bounded(self):
        self.assertEqual(score_confidence([], False), 0.3)
        self.assertLessEqual(score_confidence(["s"] * 100, True), 0.99)


class AttestationEngineTests(unittest.TestCase):
    def test_attest_hashes_content(self):
        engine = AttestationEngine()
        entry = engine.attest("build-1", "the content", ["plan"], 0.9)
        self.assertEqual(
            entry["sha256"], hashlib.sha256(b"the content").hexdigest()
        )
        self.assertEqual(entry["status"], "attested")
        self.assertEqual(entry["threshold"], CONFIDENCE_THRESHOLD)

    def test_below_threshold_is_held(self):
        engine = AttestationEngine()
        entry = engine.attest("build-1", "content", ["plan"], 0.7)
        self.assertEqual(entry["status"], "held")
        self.assertEqual(len(engine.held()), 1)

    def test_cvi_with_no_evidence_is_zero(self):
        engine = AttestationEngine()
        report = engine.cvi()
        self.assertEqual(report["cvi"], 0.0)
        self.assertEqual(report["samples"], 0)

    def test_cvi_discounts_held_attestations(self):
        engine = AttestationEngine()
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.7)  # held
        report = engine.cvi()
        self.assertEqual(report["samples"], 2)
        self.assertEqual(report["mean_confidence"], 0.8)
        self.assertEqual(report["held_ratio"], 0.5)
        self.assertEqual(report["cvi"], 0.4)

    def test_list_preserves_order_and_ids(self):
        engine = AttestationEngine()
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.5)
        entries = engine.list()
        self.assertEqual([entry["id"] for entry in entries], [1, 2])
        self.assertEqual(len(engine.held()), 1)


if __name__ == "__main__":
    unittest.main()
