import os
import tempfile
import unittest

from server import OceanicOSService
from tool_plugins import CalendarTools, WorkspaceTools, install_tool_plugins


class WorkspaceToolsTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="oceanicos-ws-")
        self.workspace = WorkspaceTools(self.root)

    def test_write_read_and_list(self):
        written = self.workspace.write_file(
            {"path": "notes/hello.md", "content": "Reality before assumption."}
        )
        self.assertTrue(written["written"])

        read = self.workspace.read_file({"path": "notes/hello.md"})
        self.assertEqual(read["content"], "Reality before assumption.")

        listed = self.workspace.list_files({})
        self.assertEqual(listed["files"], ["notes/hello.md"])
        self.assertEqual(listed["count"], 1)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.workspace.write_file({"path": "../escape.txt", "content": "nope"})
        with self.assertRaises(ValueError):
            self.workspace.read_file({"path": "../../etc/hostname"})

    def test_reading_missing_file_raises(self):
        with self.assertRaises(KeyError):
            self.workspace.read_file({"path": "missing.txt"})


class CalendarToolsTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.calendar = CalendarTools(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_list_events(self):
        event = self.calendar.add_event(
            {"title": "Charter review", "when": "2026-08-01T10:00:00Z"}
        )
        self.assertEqual(event["id"], 1)

        events = self.calendar.list_events({})
        self.assertEqual(events["count"], 1)
        self.assertEqual(events["events"][0]["title"], "Charter review")

    def test_event_requires_title_and_when(self):
        with self.assertRaises(ValueError):
            self.calendar.add_event({"title": "No time"})


class InstallToolPluginsTests(unittest.TestCase):
    def test_plugins_register_on_service(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        root = tempfile.mkdtemp(prefix="oceanicos-ws-")
        try:
            service = OceanicOSService(handle.name)
            install_tool_plugins(service, root)
            tool_names = {tool["name"] for tool in service.list_tools()}
            self.assertTrue(
                {"file_list", "file_read", "file_write", "calendar_add", "calendar_list"}
                <= tool_names
            )

            service.invoke_tool("file_write", {"path": "a.txt", "content": "hi"})
            listed = service.invoke_tool("file_list", {})
            self.assertEqual(listed["files"], ["a.txt"])

            service.invoke_tool(
                "calendar_add", {"title": "Sync", "when": "2026-08-02T09:00:00Z"}
            )
            events = service.invoke_tool("calendar_list", {})
            self.assertEqual(events["count"], 1)
        finally:
            os.remove(handle.name)


if __name__ == "__main__":
    unittest.main()
