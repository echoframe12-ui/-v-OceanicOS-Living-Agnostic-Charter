import unittest

from models import ModelAdapter, ModelRouter, strategy_literal
from rules import APPROVE, REVISE, Rule, RulesAdapter, RulesEngine


class RulesEngineTests(unittest.TestCase):
    def test_clean_prompt_approves_with_no_fired_rules(self):
        result = RulesEngine().evaluate("Plan the charter build with context provided")
        self.assertEqual(result["verdict"], APPROVE)
        self.assertEqual(result["fired"], [])

    def test_empty_prompt_fires_the_empty_rule(self):
        result = RulesEngine().evaluate("   ")
        self.assertEqual(result["verdict"], REVISE)
        self.assertIn("empty", result["fired"])

    def test_no_verb_fires_and_explains(self):
        result = RulesEngine().evaluate("the thing over there")
        self.assertEqual(result["verdict"], REVISE)
        self.assertIn("no_actionable_verb", result["fired"])
        # the reason travels with the verdict — the panel member explains itself
        self.assertTrue(all(reason for reason in result["reasons"]))

    def test_unbounded_scope_fires(self):
        result = RulesEngine().evaluate("build everything")
        self.assertIn("unbounded_scope", result["fired"])

    def test_long_prompt_without_context_fires(self):
        prompt = "please build and design and ship the whole platform end to end now today"
        result = RulesEngine().evaluate(prompt)
        self.assertIn("long_without_context", result["fired"])
        # the same prompt with 'context' stated does not fire that rule
        cleared = RulesEngine().evaluate(prompt + " with context")
        self.assertNotIn("long_without_context", cleared["fired"])

    def test_custom_rules_are_honored(self):
        only = [Rule("banned", "no foo", lambda p: "foo" in p)]
        engine = RulesEngine(rules=only)
        self.assertEqual(engine.evaluate("foo")["verdict"], REVISE)
        self.assertEqual(engine.evaluate("build it")["verdict"], APPROVE)
        self.assertEqual(engine.evaluate("foo")["rules_evaluated"], 1)


class RulesAdapterTests(unittest.TestCase):
    def test_adapter_always_matches(self):
        self.assertTrue(RulesAdapter().matches("anything at all"))

    def test_generate_carries_fired_rules_and_reasons(self):
        result = RulesAdapter().generate("everything")
        self.assertEqual(result["provider"], "rules-engine")
        self.assertEqual(result["verdict"], REVISE)
        self.assertIn("unbounded_scope", result["rules_fired"])
        self.assertTrue(result["reasons"])

    def test_describe_matches_the_model_adapter_shape(self):
        described = RulesAdapter().describe()
        self.assertEqual(set(described), {"name", "provider", "keywords"})

    def test_panel_only_engine_anchors_panels_but_never_routes_alone(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo", strategy=strategy_literal))
        router.register(RulesAdapter())
        # single route never resolves to the panel-only rules engine
        self.assertEqual(router.route("anything here")["adapter"], "local")
        # but the panel includes it
        panel = router.route_all("anything here", panel=2)
        self.assertIn("rules-engine", panel["adapters"])


if __name__ == "__main__":
    unittest.main()
