import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import oceanic_os
from attestation import CONFIDENCE_THRESHOLD, AttestationEngine


class BootTests(unittest.TestCase):
    def test_boot_reports_the_live_stack(self):
        report = oceanic_os.boot("boot/init.v1", stateless=True)
        self.assertTrue(report["manifest_present"])
        self.assertIsNotNone(report["manifest_sha256"])
        self.assertEqual(report["state"], "stateless")
        # the report reflects live components, not the manifest's declared values
        self.assertEqual(report["layers"]["backend"]["panel"], 3)
        self.assertEqual(
            report["layers"]["backend"]["confidence_threshold"], CONFIDENCE_THRESHOLD
        )
        self.assertTrue(report["anchor_present"])
        self.assertEqual(report["exit"], 0)

    def test_boot_states_the_identity_lineage(self):
        report = oceanic_os.boot("boot/init.v1", stateless=True)
        self.assertEqual(report["identity"][0], "/")
        self.assertEqual(len(report["identity"]), 4)
        self.assertIn("Living Agnostic Charter", report["identity"])

    def test_boot_names_every_layer(self):
        report = oceanic_os.boot("boot/init.v1", stateless=True)
        self.assertEqual(
            set(report["layers"]),
            {"frontend", "backend", "kernel", "operator"},
        )

    def test_missing_manifest_still_boots(self):
        report = oceanic_os.boot("boot/does-not-exist.v1", stateless=True)
        self.assertFalse(report["manifest_present"])
        self.assertIsNone(report["manifest_sha256"])
        self.assertEqual(report["exit"], 0)  # the system continues regardless

    def test_main_exits_zero_and_prints_a_report(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = oceanic_os.main(
                ["--boot", "boot/init.v1", "--state", "stateless", "--exit", "0"]
            )
        self.assertEqual(code, 0)
        output = buffer.getvalue()
        self.assertIn("OceanicOS", output)
        self.assertIn("0xΩ∞v", output)
        self.assertIn("Ω∞v Compiler", output)  # the lineage tree is printed
        self.assertIn("continues", output)

    def test_main_json_mode_emits_the_raw_report(self):
        import json

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = oceanic_os.main(["--boot", "boot/init.v1", "--json"])
        self.assertEqual(code, 0)
        report = json.loads(buffer.getvalue())
        self.assertEqual(report["status"], "continues")


class SubcommandTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.workspace = tempfile.mkdtemp(prefix="oceanicos-cli-")
        self._prev_db = os.environ.get("OCEANICOS_DB")
        self._prev_ws = os.environ.get("OCEANICOS_WORKSPACE")
        os.environ["OCEANICOS_DB"] = self.db_path
        os.environ["OCEANICOS_WORKSPACE"] = self.workspace

    def tearDown(self):
        for key, prev in (("OCEANICOS_DB", self._prev_db), ("OCEANICOS_WORKSPACE", self._prev_ws)):
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _run(self, argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = oceanic_os.main(argv)
        return code, buffer.getvalue()

    def test_verify_on_intact_ledger_exits_zero(self):
        AttestationEngine(self.db_path).attest("a", "c", [], 0.9)
        code, out = self._run(["verify"])
        self.assertEqual(code, 0)
        self.assertIn("INTACT", out)

    def test_verify_json_mode(self):
        code, out = self._run(["verify", "--json"])
        self.assertEqual(code, 0)
        self.assertIn("intact", json.loads(out))

    def test_stats_prints_totals(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "1", [], 0.9)
        engine.attest("b", "2", [], 0.5)
        code, out = self._run(["stats"])
        self.assertEqual(code, 0)
        self.assertIn("attestations: 2", out)

    def test_ready_probes_dependencies(self):
        code, out = self._run(["ready"])
        self.assertEqual(code, 0)
        self.assertIn("ready: True", out)

    def test_unknown_command_returns_two(self):
        code, out = self._run(["nonsense"])
        self.assertEqual(code, 2)
        self.assertIn("unknown command", out)

    def test_leading_flag_still_boots(self):
        code, out = self._run(["--json"])  # no subcommand -> boot
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "continues")

    def test_gate_passes_on_intact_ledger(self):
        AttestationEngine(self.db_path).attest("a", "c", [], 0.9)
        code, out = self._run(["gate"])
        self.assertEqual(code, 0)
        self.assertIn("PASS", out)

    def test_gate_fails_below_cvi_floor(self):
        AttestationEngine(self.db_path).attest("a", "c", [], 0.5)  # held, CVI 0
        code, out = self._run(["gate", "--min-cvi", "0.74"])
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)
        self.assertIn("below floor", out)

    def test_gate_requires_trustworthy(self):
        # intact but unsealed -> not trustworthy -> fails when required
        AttestationEngine(self.db_path).attest("a", "c", [], 0.9)
        code, out = self._run(["gate", "--require-trustworthy"])
        self.assertEqual(code, 1)
        self.assertIn("not trustworthy", out)

    def test_gate_json_reports_policy_and_reasons(self):
        AttestationEngine(self.db_path).attest("a", "c", [], 0.5)
        code, out = self._run(["gate", "--min-cvi", "0.9", "--json"])
        report = json.loads(out)
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])
        self.assertEqual(report["policy"]["min_cvi"], 0.9)
        self.assertTrue(report["reasons"])

    def test_gate_fails_below_source_coverage_floor(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "1", ["plan"], 0.9)  # sourced
        engine.attest("b", "2", [], 0.9)         # no source -> coverage 0.5
        code, out = self._run(["gate", "--min-sourced", "0.75"])
        self.assertEqual(code, 1)
        self.assertIn("sourced_ratio", out)
        # passes when the floor is met
        code_ok, _ = self._run(["gate", "--min-sourced", "0.5"])
        self.assertEqual(code_ok, 0)

    def test_gate_max_held_pending(self):
        engine = AttestationEngine(self.db_path)
        engine.attest("a", "1", [], 0.4)  # held
        engine.attest("b", "2", [], 0.3)  # held -> 2 pending
        code, out = self._run(["gate", "--max-held-pending", "1"])
        self.assertEqual(code, 1)
        self.assertIn("held_pending 2 over limit 1", out)
        code_ok, _ = self._run(["gate", "--max-held-pending", "2"])
        self.assertEqual(code_ok, 0)

    def test_gate_no_sla_breach(self):
        from unittest.mock import patch
        from datetime import datetime, timezone
        engine = AttestationEngine(self.db_path)
        old = datetime(2000, 1, 1, tzinfo=timezone.utc)
        # attest a held item timestamped in the distant past — the hash is
        # computed over that old created_at, so the chain stays intact
        with patch("attestation.datetime") as m:
            m.now.return_value = old
            engine.attest("a", "1", [], 0.4)  # held
        self.assertTrue(engine.verify_chain()["intact"])  # not a chain break
        prev = os.environ.get("OCEANICOS_HELD_SLA_SECONDS")
        os.environ["OCEANICOS_HELD_SLA_SECONDS"] = "3600"
        try:
            code, out = self._run(["gate", "--no-sla-breach"])
        finally:
            if prev is None:
                os.environ.pop("OCEANICOS_HELD_SLA_SECONDS", None)
            else:
                os.environ["OCEANICOS_HELD_SLA_SECONDS"] = prev
        self.assertEqual(code, 1)
        self.assertIn("past the review SLA", out)


if __name__ == "__main__":
    unittest.main()
