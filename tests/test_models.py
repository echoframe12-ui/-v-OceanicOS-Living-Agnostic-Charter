import unittest

from models import (
    ModelAdapter,
    ModelRouter,
    strategy_literal,
    strategy_optimist,
    strategy_skeptic,
)


class VerdictStrategyTests(unittest.TestCase):
    def test_optimist_approves_forward_intent(self):
        self.assertEqual(strategy_optimist("Plan the build"), "approve")
        self.assertEqual(strategy_optimist("random thoughts here"), "revise")

    def test_skeptic_needs_evidence(self):
        self.assertEqual(strategy_skeptic("attested and verified"), "approve")
        self.assertEqual(strategy_skeptic("Plan the build"), "revise")

    def test_literal_approves_only_short_prompts(self):
        self.assertEqual(strategy_literal("ship it"), "approve")
        self.assertEqual(strategy_literal("this is a much longer prompt"), "revise")


class ModelRouterTests(unittest.TestCase):
    def test_router_uses_registered_adapter(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        result = router.route("hello")
        self.assertEqual(result["adapter"], "local")
        self.assertEqual(result["provider"], "demo")

    def test_router_routes_by_keyword(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        router.register(ModelAdapter("reasoning", "demo", keywords=["plan", "charter"]))

        matched = router.route("Draft a charter update")
        self.assertEqual(matched["adapter"], "reasoning")

        fallback = router.route("hello")
        self.assertEqual(fallback["adapter"], "local")

    def test_route_all_surfaces_real_dissent(self):
        router = ModelRouter()
        router.register(ModelAdapter("optimist", "demo", keywords=["plan"], strategy=strategy_optimist))
        router.register(ModelAdapter("skeptic", "demo", keywords=["plan"], strategy=strategy_skeptic))

        # "Plan the build": optimist approves (sees "plan"/"build"), skeptic revises (no evidence)
        consensus = router.route_all("Plan the build")
        self.assertEqual(consensus["adapters"], ["optimist", "skeptic"])
        self.assertEqual(consensus["verdicts"], ["approve", "revise"])
        self.assertTrue(consensus["dissent"])
        self.assertEqual(consensus["distribution"], {"approve": 1, "revise": 1})

    def test_route_all_reports_consensus_when_verdicts_agree(self):
        router = ModelRouter()
        router.register(ModelAdapter("optimist", "demo", keywords=["plan"], strategy=strategy_optimist))
        router.register(ModelAdapter("skeptic", "demo", keywords=["plan"], strategy=strategy_skeptic))

        # "Plan the verified build": optimist approves (plan/build), skeptic approves (verified)
        consensus = router.route_all("Plan the verified build")
        self.assertEqual(consensus["verdicts"], ["approve", "approve"])
        self.assertFalse(consensus["dissent"])
        self.assertEqual(consensus["majority"], "approve")

    def test_route_all_falls_back_to_default(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo", strategy=strategy_literal))
        router.register(ModelAdapter("reasoning", "demo", keywords=["plan"], strategy=strategy_optimist))

        consensus = router.route_all("hello there friend")
        self.assertEqual(consensus["adapters"], ["local"])
        self.assertFalse(consensus["dissent"])

    def test_route_all_panel_fills_the_bench(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo", strategy=strategy_literal))
        router.register(ModelAdapter("reasoning", "demo", keywords=["plan"], strategy=strategy_optimist))
        router.register(ModelAdapter("skeptic", "demo", keywords=["verify"], strategy=strategy_skeptic))

        consensus = router.route_all("Plan the build carefully now", panel=3)
        self.assertEqual(len(consensus["adapters"]), 3)
        self.assertEqual(consensus["adapters"][0], "reasoning")
        # reasoning approves (plan/build), local revises (>4 words), skeptic revises (no evidence)
        self.assertTrue(consensus["dissent"])
        self.assertIn("majority", consensus)

    def test_router_lists_adapters(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        router.register(ModelAdapter("reasoning", "demo", keywords=["plan"]))
        adapters = router.list_adapters()
        self.assertEqual(len(adapters), 2)
        self.assertEqual(adapters[0]["name"], "local")
        self.assertEqual(adapters[1]["keywords"], ["plan"])


if __name__ == "__main__":
    unittest.main()
