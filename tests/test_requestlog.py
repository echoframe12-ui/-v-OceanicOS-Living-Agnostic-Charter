import unittest

import requestlog


class CleanRequestIdTests(unittest.TestCase):
    def test_mints_an_id_when_absent(self):
        rid = requestlog.clean_request_id(None)
        self.assertTrue(rid)
        self.assertEqual(len(rid), 16)

    def test_preserves_a_valid_id(self):
        self.assertEqual(requestlog.clean_request_id("trace-abc.123_XYZ"), "trace-abc.123_XYZ")

    def test_strips_log_injection_characters(self):
        # newlines / spaces / control chars must not survive into the log line
        rid = requestlog.clean_request_id("abc\n injected LINE\t123")
        self.assertNotIn("\n", rid)
        self.assertNotIn(" ", rid)
        self.assertEqual(rid, "abcinjectedLINE123")

    def test_caps_length(self):
        self.assertEqual(len(requestlog.clean_request_id("x" * 500)), 64)

    def test_all_invalid_falls_back_to_a_minted_id(self):
        rid = requestlog.clean_request_id("\n\n   \t")
        self.assertEqual(len(rid), 16)  # sanitized to empty -> minted


class AccessRecordTests(unittest.TestCase):
    def test_record_shape(self):
        rec = requestlog.access_record("rid1", "GET", "/cvi", 200, "alice", 12.5)
        self.assertEqual(
            rec,
            {
                "request_id": "rid1",
                "method": "GET",
                "path": "/cvi",
                "status": 200,
                "actor": "alice",
                "latency_ms": 12.5,
            },
        )


if __name__ == "__main__":
    unittest.main()
