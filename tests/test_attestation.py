import hashlib
import unittest

from attestation import (
    CONFIDENCE_THRESHOLD,
    AttestationEngine,
    consensus_delta,
    score_confidence,
)


class ConsensusDeltaTests(unittest.TestCase):
    def test_unanimous_approve_raises(self):
        self.assertEqual(consensus_delta(["approve", "approve", "approve"]), 0.1)

    def test_unanimous_revise_penalizes_hardest(self):
        self.assertEqual(consensus_delta(["revise", "revise", "revise"]), -0.2)

    def test_split_leans_to_the_majority(self):
        self.assertEqual(consensus_delta(["approve", "approve", "revise"]), 0.05)
        self.assertEqual(consensus_delta(["revise", "revise", "approve"]), -0.1)

    def test_abstentions_do_not_move_the_score(self):
        self.assertEqual(consensus_delta(["abstain"]), 0.0)
        self.assertEqual(consensus_delta([]), 0.0)


class ScoreConfidenceTests(unittest.TestCase):
    def test_more_evidence_means_more_confidence(self):
        low = score_confidence(["plan"], True)
        high = score_confidence(["plan", "workflow", "route", "agent"], True)
        self.assertGreater(high, low)

    def test_consensus_can_cross_the_threshold_in_both_directions(self):
        eight = ["s"] * 8
        # a well-evidenced build (base 0.9 with context) is attested on its own,
        # but unanimous "revise" pulls it below the hold line
        self.assertGreaterEqual(score_confidence(eight, True), CONFIDENCE_THRESHOLD)
        self.assertLess(
            score_confidence(eight, True, consensus=-0.2), CONFIDENCE_THRESHOLD
        )
        # a context-free build (base 0.7) is held on its own, but unanimous
        # "approve" lifts it back over the line
        self.assertLess(score_confidence(eight, False), CONFIDENCE_THRESHOLD)
        self.assertGreaterEqual(
            score_confidence(eight, False, consensus=0.1), CONFIDENCE_THRESHOLD
        )

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

    def test_attestations_are_scoped_by_actor(self):
        engine = AttestationEngine()
        engine.attest("a", "one", [], 0.9, actor="alice")
        engine.attest("b", "two", [], 0.9, actor="bob")
        self.assertEqual(len(engine.list()), 2)
        self.assertEqual(len(engine.list(actor="alice")), 1)
        self.assertEqual(engine.list(actor="alice")[0]["actor"], "alice")

    def test_cvi_scopes_to_actor(self):
        engine = AttestationEngine()
        engine.attest("a", "one", [], 0.9, actor="alice")
        engine.attest("b", "two", [], 0.5, actor="bob")  # held
        self.assertEqual(engine.cvi(actor="alice")["cvi"], 0.9)
        self.assertEqual(engine.cvi(actor="bob")["held_ratio"], 1.0)

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
