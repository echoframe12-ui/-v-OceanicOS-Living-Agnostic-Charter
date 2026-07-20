import unittest

import openapi
from app import app


class OpenApiGenerateTests(unittest.TestCase):
    def setUp(self):
        self.spec = openapi.generate(
            app.url_map, app.view_functions, title="Test API", version="9.9"
        )

    def test_valid_skeleton(self):
        self.assertEqual(self.spec["openapi"], "3.0.3")
        self.assertEqual(self.spec["info"]["title"], "Test API")
        self.assertEqual(self.spec["info"]["version"], "9.9")
        self.assertTrue(self.spec["paths"])

    def test_known_path_has_get_with_summary(self):
        cvi = self.spec["paths"]["/cvi"]
        self.assertIn("get", cvi)
        self.assertTrue(cvi["get"]["summary"])
        self.assertEqual(cvi["get"]["operationId"], "get_composite_verification_index")

    def test_parameterized_path_types_its_argument(self):
        op = self.spec["paths"]["/attestations/{att_id}/review"]["post"]
        params = op["parameters"]
        att = next(p for p in params if p["name"] == "att_id")
        self.assertEqual(att["in"], "path")
        self.assertTrue(att["required"])
        self.assertEqual(att["schema"]["type"], "integer")

    def test_head_and_options_are_excluded(self):
        for path, item in self.spec["paths"].items():
            self.assertNotIn("head", item)
            self.assertNotIn("options", item)

    def test_static_route_is_absent(self):
        self.assertFalse(any("static" in p for p in self.spec["paths"]))

    def test_every_round_endpoint_is_documented(self):
        # the generated surface reflects endpoints added across many rounds
        for path in ("/metrics", "/cvi/history", "/rules/evaluate", "/attestations/export", "/anchor"):
            self.assertIn(path, self.spec["paths"])


if __name__ == "__main__":
    unittest.main()
