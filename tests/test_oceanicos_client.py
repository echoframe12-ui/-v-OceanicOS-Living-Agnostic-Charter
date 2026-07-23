import unittest

import app as app_module
from app import app
from oceanicos_client import OceanicOSClient, OceanicOSError


def _flask_opener(method, path, headers, json):
    """Transport that speaks to the real routes via the Flask test client."""
    resp = app.test_client().open(path, method=method, headers=headers, json=json)
    return resp.status_code, resp.get_json()


class OceanicOSClientTests(unittest.TestCase):
    def setUp(self):
        self.kai = OceanicOSClient(opener=_flask_opener)

    def test_public_reads(self):
        self.assertEqual(self.kai.health()["status"], "ok")
        self.assertIn("cvi", self.kai.cvi())
        self.assertIn("posture", self.kai.status())
        self.assertIn("records_total", self.kai.evolution())
        self.assertEqual(self.kai.doctrine()["invariant"], "Continuous Becoming")
        self.assertIn("intact", self.kai.verify())
        self.assertIn("sourced_ratio", self.kai.stats())

    def test_register_sets_token_and_enables_authed_calls(self):
        token = self.kai.register("client-analyst")
        self.assertTrue(token)
        self.assertEqual(self.kai._token, token)
        # consensus requires a token; it now works
        result = self.kai.consensus("ship it now")
        self.assertIn("dissent_score", result)
        self.assertIn("majority", result)

    def test_attest_then_read_back_via_client(self):
        att = app_module.attestation_engine.attest("client-subj", "the output", ["plan"], 0.9)
        # content-addressable lookup finds it
        found = self.kai.lookup("the output")
        self.assertTrue(found["found"])
        # receipt for the id
        receipt = self.kai.receipt(att["id"])
        self.assertEqual(receipt["attestation"]["sha256"], att["sha256"])
        # subject history
        history = self.kai.subject_history("client-subj")
        self.assertGreaterEqual(history["count"], 1)

    def test_admin_call_requires_admin_token(self):
        # without an admin token, attention is forbidden -> raises
        self.kai.register("client-member")
        with self.assertRaises(OceanicOSError) as ctx:
            self.kai.attention()
        self.assertEqual(ctx.exception.status, 403)

    def test_admin_attention_with_admin_token(self):
        app_module.auth_registry.admin_users.add("client-steward")
        try:
            self.kai.register("client-steward")
            self.assertIsInstance(self.kai.attention(), list)
        finally:
            app_module.auth_registry.admin_users.discard("client-steward")

    def test_error_raises_with_status(self):
        with self.assertRaises(OceanicOSError) as ctx:
            self.kai.receipt(999999)
        self.assertEqual(ctx.exception.status, 404)


if __name__ == "__main__":
    unittest.main()
