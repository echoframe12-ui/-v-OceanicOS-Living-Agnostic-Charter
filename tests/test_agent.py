import unittest

from agent import AgentLoop


class AgentLoopTests(unittest.TestCase):
    def test_run_emits_events(self):
        loop = AgentLoop()
        result = loop.run("Review the charter", "Governance")
        self.assertEqual(result["task"], "Review the charter")
        self.assertEqual(len(result["events"]), 3)
        self.assertEqual(loop.events()[0]["event"], "start")


if __name__ == "__main__":
    unittest.main()
