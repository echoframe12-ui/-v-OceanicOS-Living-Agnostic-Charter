import unittest

from models import ModelAdapter, ModelRouter


class ModelRouterTests(unittest.TestCase):
    def test_router_uses_registered_adapter(self):
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        result = router.route("hello")
        self.assertEqual(result["adapter"], "local")
        self.assertEqual(result["provider"], "demo")


if __name__ == "__main__":
    unittest.main()
