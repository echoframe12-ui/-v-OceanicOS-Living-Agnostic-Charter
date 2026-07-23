import os
import tempfile
import unittest

from consensus_log import ConsensusLog, dissent_score


class DissentScoreTests(unittest.TestCase):
    def test_unanimous_opinion_is_zero(self):
        self.assertEqual(dissent_score(["approve", "approve", "approve"]), 0.0)

    def test_even_split_is_half(self):
        self.assertEqual(dissent_score(["approve", "approve", "revise", "revise"]), 0.5)

    def test_abstentions_are_ignored(self):
        # two opinions, both approve -> unanimous among opinions
        self.assertEqual(dissent_score(["approve", "approve", "abstain"]), 0.0)

    def test_all_abstain_is_zero(self):
        self.assertEqual(dissent_score(["abstain", "abstain"]), 0.0)


class ConsensusLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = ConsensusLog(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _result(self, verdicts, majority, dissent):
        return {"adapters": ["a"] * len(verdicts), "verdicts": verdicts,
                "majority": majority, "dissent": dissent}

    def test_record_hashes_prompt_and_scores_dissent(self):
        entry = self.log.record("plan the charter", self._result(
            ["approve", "revise"], "approve", True))
        self.assertEqual(len(entry["prompt_sha256"]), 64)
        self.assertNotIn("plan the charter", entry["prompt_sha256"])
        self.assertEqual(entry["dissent_score"], 0.5)
        self.assertTrue(entry["dissent"])

    def test_history_is_newest_first_and_capped(self):
        for i in range(3):
            self.log.record(f"p{i}", self._result(["approve"], "approve", False))
        history = self.log.list(limit=2)
        self.assertEqual(len(history), 2)
        self.assertGreater(history[0]["id"], history[1]["id"])

    def test_stats_aggregate_dissent(self):
        self.log.record("a", self._result(["approve", "approve"], "approve", False))
        self.log.record("b", self._result(["approve", "revise"], "approve", True))
        stats = self.log.stats()
        self.assertEqual(stats["evaluations"], 2)
        self.assertEqual(stats["dissent_count"], 1)
        self.assertEqual(stats["dissent_rate"], 0.5)
        # mean of 0.0 and 0.5
        self.assertEqual(stats["mean_dissent_score"], 0.25)

    def test_empty_stats(self):
        stats = self.log.stats()
        self.assertEqual(stats["evaluations"], 0)
        self.assertEqual(stats["dissent_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
