import unittest

from models import ModelAdapter, ModelRouter


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
