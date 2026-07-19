import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from server import OceanicOSService
from tool_plugins import (
    CalendarTools,
    GitHubTools,
    WorkspaceTools,
    install_tool_plugins,
)


def fake_response(payload):
    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    return FakeResponse(json.dumps(payload).encode())


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


class GitHubToolsTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.github = GitHubTools(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_repo_info_shapes_and_caches(self):
        api_payload = {
            "full_name": "octocat/hello",
            "description": "demo",
            "stargazers_count": 42,
            "forks_count": 7,
            "default_branch": "main",
            "open_issues_count": 3,
        }
        with patch("tool_plugins.urllib.request.urlopen", return_value=fake_response(api_payload)):
            result = self.github.repo_info({"owner": "octocat", "repo": "hello"})

        self.assertEqual(result["full_name"], "octocat/hello")
        self.assertEqual(result["stars"], 42)
        self.assertEqual(result["source"], "github_api")

    def test_network_failure_falls_back_to_ground_truth(self):
        api_payload = {"full_name": "octocat/hello", "stargazers_count": 42}
        with patch("tool_plugins.urllib.request.urlopen", return_value=fake_response(api_payload)):
            self.github.repo_info({"owner": "octocat", "repo": "hello"})

        offline = urllib.error.URLError("network unreachable")
        with patch("tool_plugins.urllib.request.urlopen", side_effect=offline):
            result = self.github.repo_info({"owner": "octocat", "repo": "hello"})

        self.assertEqual(result["source"], "ground_truth_cache")
        self.assertTrue(result["stale"])
        self.assertEqual(result["full_name"], "octocat/hello")
        self.assertIn("fetched_at", result)

    def test_network_failure_without_cache_is_structured_error(self):
        offline = urllib.error.URLError("network unreachable")
        with patch("tool_plugins.urllib.request.urlopen", side_effect=offline):
            result = self.github.repo_info({"owner": "octocat", "repo": "nocache"})
        self.assertEqual(result["error"], "connection_error")

    def test_issues_filter_out_pull_requests(self):
        api_payload = [
            {"number": 1, "title": "Real issue", "state": "open"},
            {"number": 2, "title": "A PR", "state": "open", "pull_request": {}},
        ]
        with patch("tool_plugins.urllib.request.urlopen", return_value=fake_response(api_payload)):
            result = self.github.list_issues({"owner": "octocat", "repo": "hello"})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["issues"][0]["title"], "Real issue")

    def test_missing_owner_or_repo_raises(self):
        with self.assertRaises(ValueError):
            self.github.repo_info({"owner": "octocat"})


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
