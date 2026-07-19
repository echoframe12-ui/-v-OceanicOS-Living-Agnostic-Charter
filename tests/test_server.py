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

    def test_custom_tools_can_be_registered(self):
        self.service.register_tool("shout", lambda payload: {"output": payload.get("text", "").upper()})
        tools = {tool["name"] for tool in self.service.list_tools()}
        self.assertIn("shout", tools)
        result = self.service.invoke_tool("shout", {"text": "hello"})
        self.assertEqual(result["output"], "HELLO")

    def test_timestamp_and_word_count_tools(self):
        tools = {tool["name"] for tool in self.service.list_tools()}
        self.assertIn("timestamp", tools)
        self.assertIn("word_count", tools)

        stamp = self.service.invoke_tool("timestamp", {})
        self.assertIn("T", stamp["output"])

        count = self.service.invoke_tool("word_count", {"text": "reality before assumption"})
        self.assertEqual(count["output"], 3)

    def test_builds_can_be_recorded_and_listed(self):
        entry = self.service.record_build(
            "Build the charter platform",
            "testing",
            "build-the-charter-platform",
            ["plan", "workflow"],
        )
        self.assertEqual(entry["id"], 1)
        self.assertIn("created_at", entry)

        builds = self.service.list_builds()
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["task"], "Build the charter platform")
        self.assertEqual(builds[0]["stages"], ["plan", "workflow"])

    def test_builds_persist_across_service_instances(self):
        self.service.record_build("First build", "testing", "first-build", ["plan"])
        reopened = OceanicOSService(self.temp_db.name)
        builds = reopened.list_builds()
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["artifact"], "first-build")


if __name__ == "__main__":
    unittest.main()
