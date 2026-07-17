import os
import tempfile
import unittest

from server import OceanicOSService


class OceanicOSServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.service = OceanicOSService(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_health_reports_ok(self):
        self.assertEqual(self.service.health()["status"], "ok")

    def test_plan_is_structured(self):
        result = self.service.create_plan("Draft the charter update")
        self.assertIn("task", result)
        self.assertIn("steps", result)
        self.assertGreaterEqual(len(result["steps"]), 3)

    def test_memory_can_be_stored_and_retrieved(self):
        self.service.store_memory({"text": "Need a review process", "source": "issue"})
        matches = self.service.search_memory("review")
        self.assertTrue(matches)
        self.assertIn("Need a review process", matches[0]["text"])

    def test_tools_can_be_listed_and_invoked(self):
        tools = self.service.list_tools()
        self.assertTrue(any(tool["name"] == "echo" for tool in tools))
        result = self.service.invoke_tool("echo", {"message": "hello"})
        self.assertEqual(result["output"], "hello")

    def test_plugins_can_be_registered_and_listed(self):
        self.service.register_plugin("github", {"type": "tool", "enabled": True})
        plugins = self.service.list_plugins()
        self.assertTrue(any(plugin["name"] == "github" for plugin in plugins))


if __name__ == "__main__":
    unittest.main()
