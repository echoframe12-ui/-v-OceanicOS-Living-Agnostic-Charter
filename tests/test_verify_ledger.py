import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

from attestation import GENESIS_HASH, AttestationEngine, link_hash
from verify_ledger import verify_bundle

KEY = "operator-secret"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_bundle(db_path, key=KEY, checkpoint=True):
    engine = AttestationEngine(db_path, signing_key=key)
    engine.attest("a", "one", ["plan"], 0.9)
    engine.attest("b", "two", [], 0.9)
    if checkpoint:
        engine.checkpoint()
    return engine.export()


class VerifyBundleTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.bundle = _make_bundle(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_good_bundle_is_intact_and_trustworthy(self):
        report = verify_bundle(self.bundle, key=KEY)
        self.assertTrue(report["intact"])
        self.assertTrue(report["checkpointed"])
        self.assertTrue(report["checkpoint"]["signature_valid"])
        self.assertTrue(report["trustworthy"])

    def test_good_bundle_without_key_is_intact_but_unsigned(self):
        report = verify_bundle(self.bundle, key=None)
        self.assertTrue(report["intact"])
        # the chain still checks out; the signature just isn't validated
        self.assertFalse(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_editing_an_attestation_breaks_the_chain(self):
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["confidence"] = 0.1
        report = verify_bundle(tampered, key=KEY)
        self.assertFalse(report["intact"])
        self.assertEqual(report["broken_at"], tampered["attestations"][0]["id"])

    def test_recomputed_forward_rewrite_is_caught_by_the_seal(self):
        # rebuild the chain forward around an edit so the walk passes, exactly
        # as an attacker with the bundle would — the stale sealed head catches it
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["subject"] = "tampered"
        prev = GENESIS_HASH
        for entry in tampered["attestations"]:
            entry["prev_hash"] = prev
            entry["entry_hash"] = link_hash(prev, entry)
            prev = entry["entry_hash"]
        report = verify_bundle(tampered, key=KEY)
        self.assertTrue(report["intact"])  # chain walk fooled
        self.assertFalse(report["checkpoint"]["head_reproduced"])
        self.assertFalse(report["trustworthy"])

    def test_wrong_key_fails_the_signature(self):
        report = verify_bundle(self.bundle, key="not-the-key")
        self.assertFalse(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_bundle_without_a_checkpoint_reports_uncheckpointed(self):
        engine_path = self.db_path + ".2"
        try:
            bundle = _make_bundle(engine_path, checkpoint=False)
            report = verify_bundle(bundle, key=KEY)
            self.assertTrue(report["intact"])
            self.assertFalse(report["checkpointed"])
        finally:
            if os.path.exists(engine_path):
                os.remove(engine_path)


class VerifyLedgerCliTests(unittest.TestCase):
    """The script must run as a standalone integrity gate: exit 0 good, 1 tampered."""

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.bundle = _make_bundle(self.db_path)
        bundle_handle = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w"
        )
        json.dump(self.bundle, bundle_handle)
        bundle_handle.close()
        self.bundle_path = bundle_handle.name

    def tearDown(self):
        for path in (self.db_path, self.bundle_path):
            if os.path.exists(path):
                os.remove(path)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "verify_ledger.py", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_exit_zero_for_a_good_bundle(self):
        result = self._run("--key", KEY, self.bundle_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"trustworthy": true', result.stdout)

    def test_exit_nonzero_for_a_tampered_bundle(self):
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["confidence"] = 0.1
        with open(self.bundle_path, "w") as handle:
            json.dump(tampered, handle)
        result = self._run("--key", KEY, self.bundle_path)
        self.assertEqual(result.returncode, 1)
        self.assertIn('"intact": false', result.stdout)


if __name__ == "__main__":
    unittest.main()
