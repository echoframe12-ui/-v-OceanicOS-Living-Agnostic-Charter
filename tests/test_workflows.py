import unittest

from workflows import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()

    def test_create_and_execute_workflow(self):
        self.engine.create_workflow(
            "review",
            [
                {"name": "collect", "type": "tool"},
                {"name": "summarize", "type": "reason"},
            ],
        )
        workflow = self.engine.get_workflow("review")
        self.assertEqual(workflow["name"], "review")
        self.assertEqual(len(workflow["steps"]), 2)
        executed = self.engine.execute_workflow("review")
        self.assertTrue(executed["executed"])


if __name__ == "__main__":
    unittest.main()
