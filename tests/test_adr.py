import unittest

import adr


class AdrTests(unittest.TestCase):
    def test_lists_all_records_in_order(self):
        records = adr.list_adr()
        self.assertGreaterEqual(len(records), 30)
        numbers = [r["number"] for r in records]
        self.assertEqual(numbers, sorted(numbers))
        self.assertEqual(numbers[0], 1)

    def test_each_record_has_a_title(self):
        for record in adr.list_adr():
            self.assertTrue(record["title"])
            self.assertNotIn("#", record["title"])  # heading stripped

    def test_title_strips_the_number_prefix(self):
        # 0001 heading is "# Decision 0001: Adopt the Validated Hesitation ..."
        first = adr.get_adr(1)
        self.assertNotIn("0001", first["title"])
        self.assertNotIn("Decision", first["title"].split()[0])
        self.assertIn("Hesitation", first["title"])

    def test_get_returns_full_content(self):
        record = adr.get_adr(12)  # signed checkpoints
        self.assertEqual(record["number"], 12)
        self.assertIn("## Context", record["content"])
        self.assertIn("checkpoint", record["content"].lower())

    def test_missing_number_returns_none(self):
        self.assertIsNone(adr.get_adr(9999))


if __name__ == "__main__":
    unittest.main()
