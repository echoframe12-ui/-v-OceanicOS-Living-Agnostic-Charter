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
        self.assertEqual(response.get_json()["attestation"]["status"], "attested")

        attestations = self.client.get("/attestations")
        self.assertEqual(attestations.status_code, 200)
        self.assertTrue(attestations.get_json())

        export = self.client.get("/builds/export")
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export.content_type)
        self.assertTrue(export.get_data(as_text=True).startswith("id,task,context"))

    def test_model_consensus_endpoint(self):
        response = self.client.post(
            "/models/consensus",
            data=json.dumps({"prompt": "Plan the charter build"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("dissent", payload)
        self.assertGreaterEqual(len(payload["adapters"]), 3)
        self.assertTrue(payload["results"])

    def test_vaas_endpoints(self):
        cvi = self.client.get("/cvi")
        self.assertEqual(cvi.status_code, 200)
        self.assertIn("cvi", cvi.get_json())

        pricing = self.client.get("/pricing")
        self.assertEqual(pricing.status_code, 200)
        tiers = pricing.get_json()["tiers"]
        self.assertEqual([tier["price"] for tier in tiers], [8500, 25500, 85000])

        txt = self.client.get("/builds/export.txt")
        self.assertEqual(txt.status_code, 200)
        self.assertIn("text/plain", txt.content_type)
        self.assertIn("GROUND TRUTH", txt.get_data(as_text=True))

        observer = self.client.get("/observer")
        self.assertEqual(observer.status_code, 200)
        payload = observer.get_json()
        self.assertEqual(payload["root"], "/")
        self.assertEqual(payload["sigil"], "0xΩ∞v")
        self.assertEqual(payload["exit"], 0)
        self.assertEqual(len(payload["constitution_sha256"]), 64)

    def test_auth_register_and_whoami(self):
        registered = self.client.post(
            "/auth/register",
            data=json.dumps({"username": "operator"}),
            content_type="application/json",
        )
        self.assertEqual(registered.status_code, 200)
        token = registered.get_json()["token"]
        self.assertTrue(token)

        anon = self.client.get("/auth/whoami")
        self.assertEqual(anon.get_json()["actor"], "anonymous")

        known = self.client.get(
            "/auth/whoami", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(known.get_json()["actor"], "operator")

        users = self.client.get("/auth/users")
        self.assertTrue(any(u["username"] == "operator" for u in users.get_json()))
        self.assertNotIn("token", users.get_json()[0])

    def test_builder_run_attributes_actor(self):
        token = self.client.post(
            "/auth/register",
            data=json.dumps({"username": "builder-user"}),
            content_type="application/json",
        ).get_json()["token"]

        response = self.client.post(
            "/builder/run",
            data=json.dumps({"task": "Attributed build", "context": "Identity"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["actor"], "builder-user")

        builds = self.client.get("/builds").get_json()
        self.assertTrue(any(b["actor"] == "builder-user" for b in builds))

    def test_enforcement_mode_gates_protected_endpoints(self):
        app_module.app.config["REQUIRE_AUTH"] = True
        try:
            unauth = self.client.post(
                "/builder/run",
                data=json.dumps({"task": "Locked"}),
                content_type="application/json",
            )
            self.assertEqual(unauth.status_code, 401)

            # public endpoints stay reachable while locked
            self.assertEqual(self.client.get("/health").status_code, 200)
            self.assertEqual(self.client.get("/observer").status_code, 200)

            token = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "keyholder"}),
                content_type="application/json",
            ).get_json()["token"]
            authed = self.client.post(
                "/builder/run",
                data=json.dumps({"task": "Unlocked", "context": "ok"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(authed.status_code, 200)
            self.assertEqual(authed.get_json()["actor"], "keyholder")
        finally:
            app_module.app.config["REQUIRE_AUTH"] = False

    def test_brand_badge_is_served(self):
        response = self.client.get("/static/brand/oceanicos-badge.png")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("image/"))
        self.assertGreater(len(response.get_data()), 0)

    def test_index_renders_boot_splash(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("boot-splash", body)
        self.assertIn("/static/brand/oceanicos-badge.png", body)

    def test_node_mounts(self):
        mounted = self.client.post(
            "/nodes",
            data=json.dumps({"name": "/nigeria"}),
            content_type="application/json",
        )
        self.assertEqual(mounted.status_code, 200)
        node = mounted.get_json()
        self.assertEqual(node["mount"], "/nigeria")
        self.assertEqual(node["flux"], "high")
        self.assertTrue(node["agnostic"])

        nodes = self.client.get("/nodes")
        self.assertEqual(nodes.status_code, 200)
        self.assertTrue(any(item["name"] == "nigeria" for item in nodes.get_json()))

        empty = self.client.post(
            "/nodes", data=json.dumps({"name": ""}), content_type="application/json"
        )
        self.assertEqual(empty.status_code, 400)

        history = self.client.get("/builder/history")
        self.assertEqual(history.status_code, 200)
        self.assertTrue(history.get_json())

        builds = self.client.get("/builds")
        self.assertEqual(builds.status_code, 200)
        self.assertTrue(builds.get_json())

    def test_github_tools_are_registered(self):
        response = self.client.get("/tools")
        tool_names = {tool["name"] for tool in response.get_json()}
        self.assertIn("github_repo_info", tool_names)
        self.assertIn("github_issues", tool_names)

        missing = self.client.post(
            "/tools/github_repo_info",
            data=json.dumps({"owner": "octocat"}),
            content_type="application/json",
        )
        self.assertEqual(missing.status_code, 400)

    def test_workspace_and_calendar_tools(self):
        write = self.client.post(
            "/tools/file_write",
            data=json.dumps({"path": "api-note.txt", "content": "hello from the api"}),
            content_type="application/json",
        )
        self.assertEqual(write.status_code, 200)
        self.assertTrue(write.get_json()["written"])

        read = self.client.post(
            "/tools/file_read",
            data=json.dumps({"path": "api-note.txt"}),
            content_type="application/json",
        )
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.get_json()["content"], "hello from the api")

        escape = self.client.post(
            "/tools/file_read",
            data=json.dumps({"path": "../secrets.txt"}),
            content_type="application/json",
        )
        self.assertEqual(escape.status_code, 400)

        event = self.client.post(
            "/tools/calendar_add",
            data=json.dumps({"title": "Charter sync", "when": "2026-08-01T10:00:00Z"}),
            content_type="application/json",
        )
        self.assertEqual(event.status_code, 200)
        self.assertEqual(event.get_json()["title"], "Charter sync")

        events = self.client.post(
            "/tools/calendar_list",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(events.status_code, 200)
        self.assertGreaterEqual(events.get_json()["count"], 1)

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
