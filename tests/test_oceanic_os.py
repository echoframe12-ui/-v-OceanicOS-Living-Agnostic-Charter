import io
import unittest
from contextlib import redirect_stdout

import oceanic_os
from attestation import CONFIDENCE_THRESHOLD


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


if __name__ == "__main__":
    unittest.main()
