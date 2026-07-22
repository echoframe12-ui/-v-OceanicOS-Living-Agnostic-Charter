import json
import unittest
from unittest.mock import patch

import app as app_module
import quotas
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
        # dissent is now measured on real verdicts, not adapter identity
        self.assertEqual(len(payload["verdicts"]), len(payload["adapters"]))
        self.assertIn(payload["majority"], ("approve", "revise"))
        self.assertTrue(payload["dissent"])
        # the rules engine sits on the panel as the deterministic anchor
        self.assertIn("rules-engine", payload["adapters"])

    def test_attestations_filtering(self):
        engine = app_module.attestation_engine
        engine.attest("filter-attested", "x", [], 0.9, actor="filter-user")
        engine.attest("filter-held", "y", [], 0.5, actor="filter-user")

        held = self.client.get("/attestations?status=held&actor=filter-user").get_json()
        self.assertTrue(held)
        self.assertTrue(all(a["status"] == "held" for a in held))

        subject = self.client.get("/attestations?subject=filter-attested").get_json()
        self.assertEqual([a["subject"] for a in subject], ["filter-attested"])

        limited = self.client.get("/attestations?limit=1").get_json()
        self.assertEqual(len(limited), 1)

        # validation
        self.assertEqual(self.client.get("/attestations?status=bogus").status_code, 400)
        self.assertEqual(
            self.client.get("/attestations?min_confidence=high").status_code, 400
        )

    def test_config_is_admin_gated_and_never_leaks_the_signing_key(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("config-steward")
        original_key = engine._signing_key
        engine._signing_key = "super-secret-signing-key"
        try:
            admin = self.client.post(
                "/auth/register", data=json.dumps({"username": "config-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member = self.client.post(
                "/auth/register", data=json.dumps({"username": "config-member"}),
                content_type="application/json",
            ).get_json()["token"]

            # stewardship-gated
            self.assertEqual(
                self.client.get("/config", headers={"Authorization": f"Bearer {member}"}).status_code,
                403,
            )

            resp = self.client.get("/config", headers={"Authorization": f"Bearer {admin}"})
            self.assertEqual(resp.status_code, 200)
            cfg = resp.get_json()
            # reports the effective config
            self.assertIn("require_auth", cfg)
            self.assertIn("window_seconds", cfg["quota"])
            self.assertIn("held_sla_seconds", cfg)
            self.assertIn("checkpoint", cfg)
            self.assertTrue(cfg["signing_enabled"])  # a key is set
            self.assertTrue(cfg["model_adapters"])
            # the crux: the secret itself is nowhere in the response
            self.assertNotIn("super-secret-signing-key", json.dumps(cfg))
        finally:
            engine._signing_key = original_key
            app_module.auth_registry.admin_users.discard("config-steward")

    def test_every_response_carries_a_request_id(self):
        resp = self.client.get("/health")
        self.assertTrue(resp.headers.get("X-Request-ID"))

    def test_request_id_is_propagated_from_the_caller(self):
        resp = self.client.get("/health", headers={"X-Request-ID": "trace-xyz-1"})
        self.assertEqual(resp.headers.get("X-Request-ID"), "trace-xyz-1")

    def test_malicious_request_id_is_sanitized_not_reflected_raw(self):
        # werkzeug rejects newlines at the header level (defense in depth); the
        # sanitizer strips the characters that do get through (spaces, pipes, …)
        resp = self.client.get("/health", headers={"X-Request-ID": "a b|c<script>"})
        rid = resp.headers.get("X-Request-ID")
        self.assertNotIn(" ", rid)
        self.assertNotIn("<", rid)
        self.assertEqual(rid, "abcscript")

    def test_readyz_reports_ready(self):
        resp = self.client.get("/readyz")
        self.assertEqual(resp.status_code, 200)
        report = resp.get_json()
        self.assertTrue(report["ready"])
        self.assertTrue(report["checks"]["db"])
        self.assertTrue(report["checks"]["workspace"])
        self.assertIn("chain_intact", report)

    def test_openapi_endpoint_describes_the_live_api(self):
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        spec = resp.get_json()
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertIn("/metrics", spec["paths"])
        self.assertIn("/openapi.json", spec["paths"])  # it documents itself too

    def test_me_cvi_history_tracks_the_actor(self):
        token = self.client.post(
            "/auth/register", data=json.dumps({"username": "trend-user"}),
            content_type="application/json",
        ).get_json()["token"]
        auth = {"Authorization": f"Bearer {token}"}
        self.client.post(
            "/builder/run", data=json.dumps({"task": "my build", "context": "c"}),
            content_type="application/json", headers=auth,
        )
        series = self.client.get("/me/cvi/history", headers=auth).get_json()
        self.assertTrue(series)
        # the latest personal point matches /me/cvi
        mine = self.client.get("/me/cvi", headers=auth).get_json()["cvi"]
        self.assertEqual(series[-1]["cvi"], mine)
        self.assertEqual(series[-1]["actor"], "trend-user")
        # validation
        self.assertEqual(self.client.get("/me/cvi/history?limit=x", headers=auth).status_code, 400)

    def test_cvi_history_records_on_build_and_matches_cvi(self):
        before = len(self.client.get("/cvi/history").get_json())
        self.client.post(
            "/builder/run",
            data=json.dumps({"task": "trend build", "context": "c"}),
            content_type="application/json",
        )
        series = self.client.get("/cvi/history").get_json()
        self.assertGreater(len(series), before)
        # the latest point equals the current CVI
        current = self.client.get("/cvi").get_json()["cvi"]
        self.assertEqual(series[-1]["cvi"], current)

    def test_cvi_history_limit_and_validation(self):
        limited = self.client.get("/cvi/history?limit=1").get_json()
        self.assertLessEqual(len(limited), 1)
        self.assertEqual(self.client.get("/cvi/history?limit=nope").status_code, 400)

    def test_metrics_endpoint_exposes_prometheus_text(self):
        resp = self.client.get("/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.content_type)
        body = resp.get_data(as_text=True)
        # standard exposition shape and a few known series
        self.assertIn("# HELP oceanicos_cvi", body)
        self.assertIn("# TYPE oceanicos_cvi gauge", body)
        self.assertIn("oceanicos_chain_intact 1", body)
        self.assertIn("oceanicos_attestations_total", body)

    def test_rules_evaluate_endpoint_explains_itself(self):
        response = self.client.post(
            "/rules/evaluate",
            data=json.dumps({"prompt": "build everything"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["verdict"], "revise")
        self.assertIn("unbounded_scope", payload["fired"])
        self.assertTrue(payload["reasons"])  # the reason travels with the verdict

    def test_held_review_workflow_releases_and_lifts_cvi(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("held-steward")
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "held-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "held-member"}),
                content_type="application/json",
            ).get_json()["token"]

            # a held attestation (below the 0.74 threshold)
            held = engine.attest("held-subject", "content", [], 0.5, actor="held-member")
            self.assertEqual(held["status"], "held")

            auth = {"Authorization": f"Bearer {admin}"}

            # it shows up pending in the steward's held queue
            queue = self.client.get("/attestations/held", headers=auth).get_json()
            entry = next(a for a in queue if a["id"] == held["id"])
            self.assertEqual(entry["review_status"], "pending")

            # a non-admin cannot review
            forbidden = self.client.post(
                f"/attestations/{held['id']}/review",
                data=json.dumps({"verdict": "release", "reason": "ok"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {member}"},
            )
            self.assertEqual(forbidden.status_code, 403)

            # validation: bad verdict and empty reason are rejected
            self.assertEqual(
                self.client.post(
                    f"/attestations/{held['id']}/review",
                    data=json.dumps({"verdict": "nope", "reason": "x"}),
                    content_type="application/json",
                    headers=auth,
                ).status_code,
                400,
            )
            self.assertEqual(
                self.client.post(
                    f"/attestations/{held['id']}/review",
                    data=json.dumps({"verdict": "release", "reason": "  "}),
                    content_type="application/json",
                    headers=auth,
                ).status_code,
                400,
            )

            # missing id -> 404
            self.assertEqual(
                self.client.post(
                    "/attestations/999999/review",
                    data=json.dumps({"verdict": "release", "reason": "x"}),
                    content_type="application/json",
                    headers=auth,
                ).status_code,
                404,
            )

            cvi_before = self.client.get("/cvi").get_json()["cvi"]

            # release it, on the record with a reason
            released = self.client.post(
                f"/attestations/{held['id']}/review",
                data=json.dumps({"verdict": "release", "reason": "evidence re-checked"}),
                content_type="application/json",
                headers=auth,
            )
            self.assertEqual(released.status_code, 200)

            # the trail reads back, the queue shows released, and CVI rises
            trail = self.client.get(f"/attestations/{held['id']}/reviews").get_json()
            self.assertEqual(trail[-1]["verdict"], "release")
            queue = self.client.get("/attestations/held", headers=auth).get_json()
            entry = next(a for a in queue if a["id"] == held["id"])
            self.assertEqual(entry["review_status"], "released")
            self.assertGreater(self.client.get("/cvi").get_json()["cvi"], cvi_before)

            # the chain is untouched — reviews live in their own table
            self.assertTrue(self.client.get("/attestations/verify").get_json()["intact"])
        finally:
            app_module.auth_registry.admin_users.discard("held-steward")

    def test_held_queue_and_overview_carry_sla_aging(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("sla-steward")
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "sla-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            auth = {"Authorization": f"Bearer {admin}"}
            held = engine.attest("sla-subject", "content", [], 0.5)
            self.assertEqual(held["status"], "held")

            queue = self.client.get("/attestations/held", headers=auth).get_json()
            entry = next(a for a in queue if a["id"] == held["id"])
            self.assertEqual(entry["sla"]["state"], "pending")
            self.assertIn("age_seconds", entry["sla"])
            self.assertIn("sla_breached", entry["sla"])

            overview = self.client.get("/admin/overview", headers=auth).get_json()
            self.assertIn("held_sla_breached", overview)
            self.assertIn("held_sla_seconds", overview)
        finally:
            app_module.auth_registry.admin_users.discard("sla-steward")

    def test_reviewing_a_non_held_attestation_conflicts(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("conflict-steward")
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "conflict-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            passed = engine.attest("attested", "content", [], 0.95)  # not held
            resp = self.client.post(
                f"/attestations/{passed['id']}/review",
                data=json.dumps({"verdict": "release", "reason": "n/a"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {admin}"},
            )
            self.assertEqual(resp.status_code, 409)
        finally:
            app_module.auth_registry.admin_users.discard("conflict-steward")

    def test_verify_bundle_endpoint_checks_a_supplied_bundle(self):
        engine = app_module.attestation_engine
        engine.attest("vb-a", "one", [], 0.9)
        engine.attest("vb-b", "two", [], 0.9)
        bundle = engine.export()

        # a good bundle verifies intact
        good = self.client.post(
            "/attestations/verify-bundle",
            data=json.dumps(bundle),
            content_type="application/json",
        )
        self.assertEqual(good.status_code, 200)
        self.assertTrue(good.get_json()["intact"])

        # a tampered bundle is caught, with the broken id
        bundle["attestations"][0]["confidence"] = 0.1
        bad = self.client.post(
            "/attestations/verify-bundle",
            data=json.dumps(bundle),
            content_type="application/json",
        ).get_json()
        self.assertFalse(bad["intact"])
        self.assertEqual(bad["broken_at"], 1)

        # a malformed body is rejected
        self.assertEqual(
            self.client.post(
                "/attestations/verify-bundle",
                data=json.dumps({"not": "a bundle"}),
                content_type="application/json",
            ).status_code,
            400,
        )

    def test_attestations_verify_endpoint_reports_an_intact_chain(self):
        verify = self.client.get("/attestations/verify")
        self.assertEqual(verify.status_code, 200)
        report = verify.get_json()
        self.assertIn("intact", report)
        self.assertTrue(report["intact"])
        self.assertIsNone(report["broken_at"])

    def test_checkpoint_endpoint_seals_and_verify_reflects_it(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("chain-steward")
        original_key = engine._signing_key
        engine._signing_key = "test-signing-key"
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "chain-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "chain-member"}),
                content_type="application/json",
            ).get_json()["token"]

            # sealing the chain is an admin-only act
            forbidden = self.client.post(
                "/attestations/checkpoint",
                headers={"Authorization": f"Bearer {member}"},
            )
            self.assertEqual(forbidden.status_code, 403)

            sealed = self.client.post(
                "/attestations/checkpoint",
                headers={"Authorization": f"Bearer {admin}"},
            )
            self.assertEqual(sealed.status_code, 200)
            self.assertIn("signature", sealed.get_json())

            report = self.client.get("/attestations/verify").get_json()
            self.assertTrue(report["checkpointed"])
            self.assertTrue(report["checkpoint"]["signature_valid"])
            self.assertTrue(report["trustworthy"])
        finally:
            engine._signing_key = original_key
            app_module.auth_registry.admin_users.discard("chain-steward")

    def test_checkpoint_without_a_key_is_unavailable(self):
        engine = app_module.attestation_engine
        app_module.auth_registry.admin_users.add("keyless-steward")
        original_key = engine._signing_key
        engine._signing_key = ""
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "keyless-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            resp = self.client.post(
                "/attestations/checkpoint",
                headers={"Authorization": f"Bearer {admin}"},
            )
            self.assertEqual(resp.status_code, 503)
        finally:
            engine._signing_key = original_key
            app_module.auth_registry.admin_users.discard("keyless-steward")

    def test_anchor_endpoint_surfaces_the_failover(self):
        resp = self.client.get("/anchor")
        self.assertEqual(resp.status_code, 200)
        state = resp.get_json()
        self.assertTrue(state["present"])
        self.assertTrue(state["integrity_ok"])
        # a dated lookup answers straight from the anchor
        dated = self.client.get("/anchor?date=2019-07-04").get_json()
        self.assertIn("2019-07-04", dated["lookup"]["row"])

    def test_observer_reports_manifest_and_anchor(self):
        obs = self.client.get("/observer").get_json()
        self.assertIsNotNone(obs["manifest_sha256"])
        self.assertTrue(obs["anchor_present"])
        self.assertEqual(obs["sigil"], "0xΩ∞v")
        self.assertEqual(
            obs["identity"],
            ["/", "Ω∞v Compiler", "OceanicOS", "Living Agnostic Charter"],
        )

    def test_attestations_export_returns_a_portable_bundle(self):
        export = self.client.get("/attestations/export")
        self.assertEqual(export.status_code, 200)
        self.assertIn("application/json", export.content_type)
        bundle = export.get_json()
        self.assertEqual(bundle["version"], 1)
        self.assertIn("attestations", bundle)
        self.assertIn("checkpoints", bundle)

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

    def test_usage_is_logged_and_scoped(self):
        token = self.client.post(
            "/auth/register",
            data=json.dumps({"username": "usage-user"}),
            content_type="application/json",
        ).get_json()["token"]
        auth = {"Authorization": f"Bearer {token}"}

        self.client.post(
            "/builder/run",
            data=json.dumps({"task": "Logged build", "context": "audit"}),
            content_type="application/json",
            headers=auth,
        )

        usage = self.client.get("/me/usage", headers=auth).get_json()
        self.assertTrue(any(e["action"] == "build" for e in usage))
        self.assertTrue(all(e["actor"] == "usage-user" for e in usage))

    def test_admin_usage_is_gated_and_records_tier_changes(self):
        app_module.auth_registry.admin_users.add("audit-steward")
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "audit-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "audit-member"}),
                content_type="application/json",
            ).get_json()["token"]

            self.client.post(
                "/admin/users/audit-member/tier",
                data=json.dumps({"tier": "arbiter"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {admin}"},
            )

            # member is forbidden from the admin audit log
            forbidden = self.client.get(
                "/admin/usage", headers={"Authorization": f"Bearer {member}"}
            )
            self.assertEqual(forbidden.status_code, 403)

            events = self.client.get(
                "/admin/usage?actor=audit-member",
                headers={"Authorization": f"Bearer {admin}"},
            ).get_json()
            self.assertTrue(
                any(e["action"] == "tier_change" and e["tier"] == "arbiter" for e in events)
            )
        finally:
            app_module.auth_registry.admin_users.discard("audit-steward")

    def test_quota_block_is_audited(self):
        token = self.client.post(
            "/auth/register",
            data=json.dumps({"username": "blocked-user"}),
            content_type="application/json",
        ).get_json()["token"]
        auth = {"Authorization": f"Bearer {token}"}
        with patch.dict(quotas.TIER_LIMITS, {"attestor": 0}):
            blocked = self.client.post(
                "/builder/run",
                data=json.dumps({"task": "Nope", "context": "audit"}),
                content_type="application/json",
                headers=auth,
            )
            self.assertEqual(blocked.status_code, 429)
        usage = self.client.get("/me/usage", headers=auth).get_json()
        self.assertTrue(any(e["action"] == "quota_exceeded" for e in usage))

    def test_quota_view_and_enforcement(self):
        token = self.client.post(
            "/auth/register",
            data=json.dumps({"username": "quota-user"}),
            content_type="application/json",
        ).get_json()["token"]
        auth = {"Authorization": f"Bearer {token}"}

        quota = self.client.get("/me/quota", headers=auth).get_json()
        self.assertEqual(quota["tier"], "attestor")
        self.assertEqual(quota["used"], 0)
        self.assertFalse(quota["exceeded"])
        self.assertEqual(quota["window_seconds"], quotas.WINDOW_SECONDS)

        # tighten the attestor limit to 1 for a fast, deterministic 429 (both
        # builds land in the same window, so the second is refused)
        with patch.dict(quotas.TIER_LIMITS, {"attestor": 1}):
            first = self.client.post(
                "/builder/run",
                data=json.dumps({"task": "First", "context": "quota"}),
                content_type="application/json",
                headers=auth,
            )
            self.assertEqual(first.status_code, 200)
            # a successful build carries standard rate-limit headers, remaining
            # reflecting the slot just consumed (limit 1 -> 0 left)
            self.assertEqual(first.headers.get("X-RateLimit-Limit"), "1")
            self.assertEqual(first.headers.get("X-RateLimit-Remaining"), "0")

            blocked = self.client.post(
                "/builder/run",
                data=json.dumps({"task": "Second", "context": "quota"}),
                content_type="application/json",
                headers=auth,
            )
            self.assertEqual(blocked.status_code, 429)
            body = blocked.get_json()
            self.assertEqual(body["error"], "quota exceeded")
            self.assertEqual(body["tier"], "attestor")
            self.assertEqual(body["window_seconds"], quotas.WINDOW_SECONDS)
            self.assertIsNotNone(body["resets_at"])
            # the 429 tells the client when to come back
            self.assertEqual(blocked.headers.get("X-RateLimit-Remaining"), "0")
            self.assertIsNotNone(blocked.headers.get("Retry-After"))
            self.assertGreaterEqual(int(blocked.headers["Retry-After"]), 0)

    def test_unlimited_tier_emits_no_rate_limit_headers(self):
        app_module.auth_registry.admin_users.add("sov-steward")
        try:
            admin = self.client.post(
                "/auth/register", data=json.dumps({"username": "sov-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            sov = self.client.post(
                "/auth/register", data=json.dumps({"username": "sov-user"}),
                content_type="application/json",
            ).get_json()["token"]
            # promote the existing user; the token is unchanged by a tier change
            self.client.post(
                "/admin/users/sov-user/tier", data=json.dumps({"tier": "sovereign"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {admin}"},
            )
            resp = self.client.get("/me/quota", headers={"Authorization": f"Bearer {sov}"})
            self.assertIsNone(resp.get_json()["limit"])  # unlimited
            self.assertIsNone(resp.headers.get("X-RateLimit-Limit"))  # no ceiling to report
        finally:
            app_module.auth_registry.admin_users.discard("sov-steward")

    def test_admin_can_promote_a_users_tier(self):
        app_module.auth_registry.admin_users.add("tier-steward")
        try:
            admin = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "tier-steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "promote-me"}),
                content_type="application/json",
            ).get_json()["token"]

            promoted = self.client.post(
                "/admin/users/promote-me/tier",
                data=json.dumps({"tier": "sovereign"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {admin}"},
            )
            self.assertEqual(promoted.status_code, 200)

            quota = self.client.get(
                "/me/quota", headers={"Authorization": f"Bearer {member}"}
            ).get_json()
            self.assertEqual(quota["tier"], "sovereign")
            self.assertIsNone(quota["limit"])

            # a member cannot promote anyone
            forbidden = self.client.post(
                "/admin/users/promote-me/tier",
                data=json.dumps({"tier": "arbiter"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {member}"},
            )
            self.assertEqual(forbidden.status_code, 403)
        finally:
            app_module.auth_registry.admin_users.discard("tier-steward")

    def test_admin_role_gates_stewardship_views(self):
        app_module.auth_registry.admin_users.add("steward")
        try:
            admin_token = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "steward"}),
                content_type="application/json",
            ).get_json()["token"]
            member_token = self.client.post(
                "/auth/register",
                data=json.dumps({"username": "plain-member"}),
                content_type="application/json",
            ).get_json()["token"]

            whoami = self.client.get(
                "/auth/whoami", headers={"Authorization": f"Bearer {admin_token}"}
            ).get_json()
            self.assertEqual(whoami["role"], "admin")

            # member is forbidden from the stewardship surface
            forbidden = self.client.get(
                "/admin/overview", headers={"Authorization": f"Bearer {member_token}"}
            )
            self.assertEqual(forbidden.status_code, 403)
            anon = self.client.get("/admin/overview")
            self.assertEqual(anon.status_code, 403)

            # admin sees across actors
            overview = self.client.get(
                "/admin/overview", headers={"Authorization": f"Bearer {admin_token}"}
            )
            self.assertEqual(overview.status_code, 200)
            self.assertIn("users", overview.get_json())
            self.assertIn("actors", overview.get_json())

            users = self.client.get(
                "/admin/users", headers={"Authorization": f"Bearer {admin_token}"}
            ).get_json()
            steward_row = next(u for u in users if u["username"] == "steward")
            self.assertEqual(steward_row["role"], "admin")
            self.assertIn("builds", steward_row)
        finally:
            app_module.auth_registry.admin_users.discard("steward")

    def test_me_views_scope_to_the_authenticated_actor(self):
        def register(name):
            return self.client.post(
                "/auth/register",
                data=json.dumps({"username": name}),
                content_type="application/json",
            ).get_json()["token"]

        def run_build(token, task):
            return self.client.post(
                "/builder/run",
                data=json.dumps({"task": task, "context": "scoping"}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {token}"},
            )

        alice = register("scope-alice")
        bob = register("scope-bob")
        run_build(alice, "Alice scoped build")
        run_build(bob, "Bob scoped build")

        alice_builds = self.client.get(
            "/me/builds", headers={"Authorization": f"Bearer {alice}"}
        ).get_json()
        self.assertTrue(alice_builds)
        self.assertTrue(all(b["actor"] == "scope-alice" for b in alice_builds))
        self.assertFalse(any(b["actor"] == "scope-bob" for b in alice_builds))

        alice_att = self.client.get(
            "/me/attestations", headers={"Authorization": f"Bearer {alice}"}
        ).get_json()
        self.assertTrue(all(a["actor"] == "scope-alice" for a in alice_att))

        alice_mem = self.client.get(
            "/me/memory?query=build", headers={"Authorization": f"Bearer {alice}"}
        ).get_json()
        self.assertTrue(alice_mem)

        alice_cvi = self.client.get(
            "/me/cvi", headers={"Authorization": f"Bearer {alice}"}
        ).get_json()
        self.assertGreaterEqual(alice_cvi["samples"], 1)

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
