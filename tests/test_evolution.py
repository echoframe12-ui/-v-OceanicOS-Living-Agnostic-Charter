import unittest

import evolution


class CompoundingTests(unittest.TestCase):
    def test_structures_counts_with_totals(self):
        result = evolution.compounding({"attestations": 3, "decisions": 60})
        self.assertEqual(result["records_total"], 63)
        self.assertEqual(result["ledger_count"], 2)
        self.assertTrue(result["append_only"])
        self.assertEqual(result["invariant"], "Continuous Becoming")

    def test_each_ledger_carries_a_count_and_note(self):
        result = evolution.compounding({"attestations": 5})
        entry = result["ledgers"]["attestations"]
        self.assertEqual(entry["count"], 5)
        self.assertTrue(entry["accrues"])  # a human-facing description

    def test_empty_footprint_is_zeroed(self):
        result = evolution.compounding({})
        self.assertEqual(result["records_total"], 0)
        self.assertEqual(result["ledger_count"], 0)


if __name__ == "__main__":
    unittest.main()
