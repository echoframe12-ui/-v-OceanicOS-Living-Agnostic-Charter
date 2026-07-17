import json
import unittest
from unittest.mock import patch

import app as app_module
from app import app


class OceanicOSAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_plan_endpoint(self):
        response = self.client.post(
            "/plans",
            data=json.dumps({"task": "Draft a charter update"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("steps", response.get_json())

    def test_main_uses_environment_configuration(self):
        with patch.dict(
            "os.environ",
            {"HOST": "127.0.0.1", "PORT": "9000", "FLASK_DEBUG": "0"},
            clear=False,
        ):
            with patch.object(app_module.app, "run") as run_mock:
                app_module.main()
        run_mock.assert_called_once_with(host="127.0.0.1", port=9000, debug=False)

    def test_memory_endpoint(self):
        response = self.client.post(
            "/memory",
            data=json.dumps({"text": "Need review", "source": "api"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["stored"], True)

    def test_tool_endpoint(self):
        response = self.client.post(
            "/tools/echo",
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["output"], "hello")

    def test_workflow_endpoints(self):
        response = self.client.post(
            "/workflows",
            data=json.dumps({"name": "review", "steps": [{"name": "collect", "type": "tool"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["created"])

        fetched = self.client.get("/workflows/review")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["name"], "review")

        executed = self.client.post("/workflows/review/execute")
        self.assertEqual(executed.status_code, 200)
        self.assertTrue(executed.get_json()["executed"])

    def test_planner_endpoints(self):
        response = self.client.post(
            "/plans/execute",
            data=json.dumps({"task": "Draft the charter", "context": "Governance update"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"], "Draft the charter")

        trace = self.client.get("/plans/trace")
        self.assertEqual(trace.status_code, 200)
        self.assertTrue(trace.get_json())

    def test_model_router_endpoint(self):
        response = self.client.post(
            "/models/route",
            data=json.dumps({"prompt": "Hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["adapter"], "local")

    def test_agent_endpoints(self):
        response = self.client.post(
            "/agent/run",
            data=json.dumps({"task": "Review the charter", "context": "Governance"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"], "Review the charter")

        events = self.client.get("/agent/events")
        self.assertEqual(events.status_code, 200)
        self.assertTrue(events.get_json())

    def test_state_endpoints(self):
        response = self.client.post(
            "/state",
            data=json.dumps({"event": "start", "detail": "initialized"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)

        snapshot = self.client.get("/state")
        self.assertEqual(snapshot.status_code, 200)
        self.assertTrue(snapshot.get_json()["events"])

    def test_review_endpoints(self):
        response = self.client.post(
            "/reviews",
            data=json.dumps({"proposal": "Add a plugin", "reviewer": "maintainer"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "pending")

        approved = self.client.post("/reviews/Add%20a%20plugin/approve")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.get_json()["status"], "approved")

    def test_decision_endpoints(self):
        response = self.client.post(
            "/decisions",
            data=json.dumps({"title": "Use SQLite", "context": "Need persistence", "decision": "Store memory in SQLite"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["title"], "Use SQLite")

        decisions = self.client.get("/decisions")
        self.assertEqual(decisions.status_code, 200)
        self.assertTrue(decisions.get_json())

    def test_artifact_endpoints(self):
        response = self.client.post(
            "/artifacts",
            data=json.dumps({"name": "spec", "kind": "document", "status": "draft"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "spec")

        artifacts = self.client.get("/artifacts")
        self.assertEqual(artifacts.status_code, 200)
        self.assertTrue(artifacts.get_json())

    def test_dashboard_endpoints(self):
        response = self.client.post(
            "/dashboard",
            data=json.dumps({"title": "Plan charter", "kind": "plan", "status": "active"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)

        dashboard = self.client.get("/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertTrue(dashboard.get_json()["items"])

    def test_builder_run_endpoint(self):
        response = self.client.post(
            "/builder/run",
            data=json.dumps({"task": "Draft a charter update", "context": "Governance"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"], "Draft a charter update")
        self.assertEqual(response.get_json()["model"]["adapter"], "reasoning")
        self.assertEqual(response.get_json()["review"]["status"], "approved")
        self.assertIn("ledger", response.get_json()["stages"])

        history = self.client.get("/builder/history")
        self.assertEqual(history.status_code, 200)
        self.assertTrue(history.get_json())

        builds = self.client.get("/builds")
        self.assertEqual(builds.status_code, 200)
        self.assertTrue(builds.get_json())

    def test_models_listing_endpoint(self):
        response = self.client.get("/models")
        self.assertEqual(response.status_code, 200)
        adapters = response.get_json()
        self.assertEqual(adapters[0]["name"], "local")
        self.assertTrue(any(adapter["name"] == "reasoning" for adapter in adapters))

    def test_builder_evolve_endpoint(self):
        response = self.client.post("/builder/evolve")
        self.assertEqual(response.status_code, 200)
        report = response.get_json()
        self.assertIn("runs", report)
        self.assertIn("next_steps", report)
        self.assertTrue(report["next_steps"])

    def test_unknown_workflow_returns_404(self):
        response = self.client.get("/workflows/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_plugin_endpoints(self):
        response = self.client.post(
            "/plugins",
            data=json.dumps({"name": "github", "capabilities": ["tool", "sync"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "github")

        plugins = self.client.get("/plugins")
        self.assertEqual(plugins.status_code, 200)
        self.assertTrue(plugins.get_json())


if __name__ == "__main__":
    unittest.main()
