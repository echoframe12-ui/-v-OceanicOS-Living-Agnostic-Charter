import hashlib
import os
import sqlite3
import tempfile
import unittest

from attestation import (
    CONFIDENCE_THRESHOLD,
    GENESIS_HASH,
    AttestationEngine,
    checkpoint_signature,
    consensus_delta,
    link_hash,
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
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_attest_hashes_content(self):
        engine = AttestationEngine(self.db_path)
        entry = engine.attest("build-1", "the content", ["plan"], 0.9)
        self.assertEqual(
            entry["sha256"], hashlib.sha256(b"the content").hexdigest()
        )
        self.assertEqual(entry["status"], "attested")
        self.assertEqual(entry["threshold"], CONFIDENCE_THRESHOLD)

    def test_below_threshold_is_held(self):
        engine = AttestationEngine(self.db_path)
        entry = engine.attest("build-1", "content", ["plan"], 0.7)
        self.assertEqual(entry["status"], "held")
        self.assertEqual(len(engine.held()), 1)

    def test_cvi_with_no_evidence_is_zero(self):
        engine = AttestationEngine(self.db_path)
        report = engine.cvi()
        self.assertEqual(report["cvi"], 0.0)
        self.assertEqual(report["samples"], 0)

    def test_attestations_are_scoped_by_actor(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", [], 0.9, actor="alice")
        engine.attest("b", "two", [], 0.9, actor="bob")
        self.assertEqual(len(engine.list()), 2)
        self.assertEqual(len(engine.list(actor="alice")), 1)
        self.assertEqual(engine.list(actor="alice")[0]["actor"], "alice")

    def test_cvi_scopes_to_actor(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", [], 0.9, actor="alice")
        engine.attest("b", "two", [], 0.5, actor="bob")  # held
        self.assertEqual(engine.cvi(actor="alice")["cvi"], 0.9)
        self.assertEqual(engine.cvi(actor="bob")["held_ratio"], 1.0)

    def test_cvi_discounts_held_attestations(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.7)  # held
        report = engine.cvi()
        self.assertEqual(report["samples"], 2)
        self.assertEqual(report["mean_confidence"], 0.8)
        self.assertEqual(report["held_ratio"], 0.5)
        self.assertEqual(report["cvi"], 0.4)

    def test_list_preserves_order_and_ids(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.5)
        entries = engine.list()
        self.assertEqual([entry["id"] for entry in entries], [1, 2])
        self.assertEqual(len(engine.held()), 1)

    def test_record_is_shared_across_instances(self):
        # Two engines on one database stand in for two gunicorn workers: an
        # attestation written by one is visible — and folded into the CVI — by
        # the other. This is the whole point of persisting the record.
        worker_a = AttestationEngine(self.db_path)
        worker_b = AttestationEngine(self.db_path)
        worker_a.attest("shared", "content", ["plan"], 0.9, actor="alice")
        self.assertEqual(len(worker_b.list()), 1)
        self.assertEqual(worker_b.cvi(actor="alice")["samples"], 1)

    def test_sources_survive_the_round_trip(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", ["plan", "consensus:approve"], 0.9)
        self.assertEqual(engine.list()[0]["sources"], ["plan", "consensus:approve"])

    def test_chain_links_each_entry_to_its_predecessor(self):
        engine = AttestationEngine(self.db_path)
        first = engine.attest("a", "one", [], 0.9)
        second = engine.attest("b", "two", [], 0.9)
        self.assertEqual(first["prev_hash"], GENESIS_HASH)
        self.assertEqual(second["prev_hash"], first["entry_hash"])

    def test_verify_chain_is_intact_for_an_untouched_ledger(self):
        engine = AttestationEngine(self.db_path)
        for i in range(3):
            engine.attest(f"s{i}", f"content {i}", [], 0.9)
        report = engine.verify_chain()
        self.assertTrue(report["intact"])
        self.assertEqual(report["length"], 3)
        self.assertIsNone(report["broken_at"])

    def test_verify_chain_is_intact_for_an_empty_ledger(self):
        engine = AttestationEngine(self.db_path)
        self.assertTrue(engine.verify_chain()["intact"])

    def test_verify_chain_detects_a_retroactive_edit(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.5)  # held
        engine.attest("c", "three", [], 0.9)
        # tamper: flip the middle entry's held status straight in the database,
        # exactly as an attacker rewriting the record would
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE attestations SET status = 'attested' WHERE id = 2")
        report = engine.verify_chain()
        self.assertFalse(report["intact"])
        self.assertEqual(report["broken_at"], 2)

    def test_chain_continues_across_instances(self):
        worker_a = AttestationEngine(self.db_path)
        worker_b = AttestationEngine(self.db_path)
        a = worker_a.attest("a", "one", [], 0.9)
        b = worker_b.attest("b", "two", [], 0.9)
        self.assertEqual(b["prev_hash"], a["entry_hash"])
        self.assertTrue(worker_a.verify_chain()["intact"])


class SignedCheckpointTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_checkpoint_requires_a_signing_key(self):
        engine = AttestationEngine(self.db_path, signing_key="")
        self.assertFalse(engine.can_sign)
        engine.attest("a", "one", [], 0.9)
        with self.assertRaises(RuntimeError):
            engine.checkpoint()

    def test_checkpoint_seals_and_verifies_the_head(self):
        engine = AttestationEngine(self.db_path, signing_key="operator-secret")
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.9)
        cp = engine.checkpoint()
        report = engine.verify()
        self.assertTrue(report["trustworthy"])
        self.assertTrue(report["checkpoint"]["signature_valid"])
        self.assertTrue(report["checkpoint"]["head_reproduced"])
        self.assertEqual(report["checkpoint"]["length"], 2)
        self.assertEqual(cp["head_hash"], report["head"])

    def test_checkpoint_refuses_a_broken_chain(self):
        engine = AttestationEngine(self.db_path, signing_key="k")
        engine.attest("a", "one", [], 0.9)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE attestations SET confidence = 0.1 WHERE id = 1")
        with self.assertRaises(RuntimeError):
            engine.checkpoint()

    def test_verify_without_a_checkpoint_reports_uncheckpointed(self):
        engine = AttestationEngine(self.db_path, signing_key="k")
        engine.attest("a", "one", [], 0.9)
        report = engine.verify()
        self.assertFalse(report["checkpointed"])
        self.assertNotIn("trustworthy", report)

    def test_wrong_key_fails_signature_validation(self):
        signer = AttestationEngine(self.db_path, signing_key="the-real-key")
        signer.attest("a", "one", [], 0.9)
        signer.checkpoint()
        # a verifier holding the wrong key cannot validate the signature
        impostor = AttestationEngine(self.db_path, signing_key="a-different-key")
        report = impostor.verify()
        self.assertFalse(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_checkpoint_catches_a_recomputed_forward_rewrite(self):
        # The whole point of signing: an attacker rewrites a past entry AND
        # recomputes every later hash so the chain is internally consistent —
        # verify_chain alone would pass. The signed checkpoint still catches it,
        # because the new head no longer matches the sealed one and the attacker
        # cannot forge a signature over their forged head without the key.
        engine = AttestationEngine(self.db_path, signing_key="operator-secret")
        engine.attest("a", "one", [], 0.9)
        engine.attest("b", "two", [], 0.9)
        engine.checkpoint()  # seals head over length 2

        # attacker rewrites row 1 and rebuilds the chain forward, honestly
        rows = engine.list()
        rows[0]["subject"] = "tampered"
        prev = GENESIS_HASH
        with sqlite3.connect(self.db_path) as conn:
            for row in rows:
                new_entry_hash = link_hash(prev, row)
                conn.execute(
                    "UPDATE attestations SET subject = ?, prev_hash = ?, entry_hash = ? WHERE id = ?",
                    (row["subject"], prev, new_entry_hash, row["id"]),
                )
                prev = new_entry_hash

        report = engine.verify()
        # the chain looks internally consistent to the walk...
        self.assertTrue(report["intact"])
        # ...but the sealed head is no longer reproduced, and the signature over
        # it still validates — so the tamper is caught and trust is withdrawn
        self.assertFalse(report["checkpoint"]["head_reproduced"])
        self.assertTrue(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_list_checkpoints_returns_every_seal_in_order(self):
        engine = AttestationEngine(self.db_path, signing_key="k")
        engine.attest("a", "one", [], 0.9)
        first = engine.checkpoint()
        engine.attest("b", "two", [], 0.9)
        second = engine.checkpoint()
        checkpoints = engine.list_checkpoints()
        self.assertEqual([cp["id"] for cp in checkpoints], [first["id"], second["id"]])
        self.assertEqual(checkpoints[-1]["length"], 2)


class ExportTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_export_carries_the_whole_sealed_record(self):
        engine = AttestationEngine(self.db_path, signing_key="k")
        engine.attest("a", "one", ["plan"], 0.9)
        engine.attest("b", "two", [], 0.9)
        engine.checkpoint()
        bundle = engine.export()
        self.assertEqual(bundle["version"], 1)
        self.assertEqual(bundle["genesis"], GENESIS_HASH)
        self.assertIn("exported_at", bundle)
        self.assertEqual(len(bundle["attestations"]), 2)
        self.assertEqual(len(bundle["checkpoints"]), 1)
        self.assertEqual(bundle["attestations"][0]["sources"], ["plan"])

    def test_export_of_an_empty_ledger_is_well_formed(self):
        engine = AttestationEngine(self.db_path, signing_key="k")
        bundle = engine.export()
        self.assertEqual(bundle["attestations"], [])
        self.assertEqual(bundle["checkpoints"], [])


class CheckpointSignatureTests(unittest.TestCase):
    def test_signature_is_deterministic_and_sensitive_to_key_head_and_length(self):
        base = checkpoint_signature("key", "abc", 3)
        self.assertEqual(base, checkpoint_signature("key", "abc", 3))
        self.assertNotEqual(base, checkpoint_signature("other-key", "abc", 3))
        self.assertNotEqual(base, checkpoint_signature("key", "abcd", 3))
        self.assertNotEqual(base, checkpoint_signature("key", "abc", 4))


class LinkHashTests(unittest.TestCase):
    def test_link_hash_is_deterministic_and_prev_sensitive(self):
        entry = {
            "subject": "a", "actor": "alice", "sha256": "x", "confidence": 0.9,
            "threshold": CONFIDENCE_THRESHOLD, "status": "attested",
            "sources": [], "created_at": "2026-01-01T00:00:00+00:00",
        }
        self.assertEqual(link_hash(GENESIS_HASH, entry), link_hash(GENESIS_HASH, entry))
        self.assertNotEqual(link_hash(GENESIS_HASH, entry), link_hash("deadbeef", entry))


if __name__ == "__main__":
    unittest.main()
