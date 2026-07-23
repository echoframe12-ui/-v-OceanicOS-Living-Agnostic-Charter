import unittest

import status_digest


BASE = {
    "posture": "TRUSTWORTHY",
    "cvi": 0.9,
    "sourced_ratio": 0.75,
    "chain_intact": True,
    "trustworthy": True,
    "chain_length": 4,
    "held_pending": 1,
    "held_breached": 0,
    "checkpoint_head": "abc123",
    "generated_at": "2026-07-23T00:00:00+00:00",
}


class CanonicalTests(unittest.TestCase):
    def test_canonical_is_deterministic_and_order_independent(self):
        reordered = dict(reversed(list(BASE.items())))
        self.assertEqual(status_digest.canonical(BASE), status_digest.canonical(reordered))

    def test_canonical_ignores_extra_fields(self):
        with_extra = {**BASE, "signed": True, "signature": "x"}
        self.assertEqual(status_digest.canonical(BASE), status_digest.canonical(with_extra))


class SignVerifyTests(unittest.TestCase):
    def test_sign_then_verify_roundtrip(self):
        sig = status_digest.sign("secret", BASE)
        self.assertTrue(status_digest.verify(BASE, sig, "secret"))

    def test_wrong_key_fails(self):
        sig = status_digest.sign("secret", BASE)
        self.assertFalse(status_digest.verify(BASE, sig, "other"))

    def test_tampered_payload_fails(self):
        sig = status_digest.sign("secret", BASE)
        tampered = {**BASE, "posture": "BROKEN"}
        self.assertFalse(status_digest.verify(tampered, sig, "secret"))

    def test_no_key_never_verifies(self):
        sig = status_digest.sign("secret", BASE)
        self.assertFalse(status_digest.verify(BASE, sig, None))
        self.assertFalse(status_digest.verify(BASE, "", "secret"))


if __name__ == "__main__":
    unittest.main()
