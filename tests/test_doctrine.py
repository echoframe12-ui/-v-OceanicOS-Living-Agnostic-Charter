import importlib
import unittest
from pathlib import Path

import doctrine
from app import app

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTES = {rule.rule for rule in app.url_map.iter_rules()}


class DoctrineIntegrityTests(unittest.TestCase):
    """The Doctrine is held to its own creed: every 'shipped' claim points at code."""

    def _decision_exists(self, number: int) -> bool:
        return bool(list((REPO_ROOT / "DECISIONS").glob(f"{number:04d}-*.md")))

    def test_every_shipped_layer_cites_resolvable_code(self):
        for layer in doctrine.LAYERS:
            if not layer["shipped"]:
                continue
            ev = layer["evidence"]
            with self.subTest(layer=layer["layer"]):
                for endpoint in ev.get("endpoints", []):
                    self.assertIn(endpoint, ROUTES, f"{layer['layer']}: no route {endpoint}")
                for module in ev.get("modules", []):
                    importlib.import_module(module)  # raises if missing
                for number in ev.get("decisions", []):
                    self.assertTrue(self._decision_exists(number),
                                    f"{layer['layer']}: no DECISIONS/{number:04d}")
                for doc in ev.get("docs", []):
                    self.assertTrue((REPO_ROOT / doc).exists(), f"{layer['layer']}: missing {doc}")

    def test_unshipped_layers_are_honest(self):
        # a layer that isn't shipped must say so and explain — attest, don't assert
        unshipped = [l for l in doctrine.LAYERS if not l["shipped"]]
        self.assertTrue(unshipped, "the Doctrine should name what is not built")
        for layer in unshipped:
            with self.subTest(layer=layer["layer"]):
                self.assertIn("note", layer)
                self.assertTrue(layer["note"].strip())

    def test_summary_shape(self):
        s = doctrine.summary()
        self.assertEqual(len(s["axioms"]), 5)
        self.assertEqual(s["layers_total"], len(doctrine.LAYERS))
        self.assertEqual(s["layers_shipped"], sum(1 for l in doctrine.LAYERS if l["shipped"]))
        self.assertLess(s["layers_shipped"], s["layers_total"])  # honesty: not everything ships
        self.assertEqual(s["status"], "continues")

    def test_doctrine_md_exists(self):
        self.assertTrue((REPO_ROOT / "DOCTRINE.md").exists())


class DoctrineEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_endpoint_serves_the_doctrine(self):
        resp = self.client.get("/doctrine")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["invariant"], "Continuous Becoming")
        self.assertIn("checksum", data)
        self.assertEqual(data["exit"], 0)
        self.assertTrue(any(not l["shipped"] for l in data["layers"]))


if __name__ == "__main__":
    unittest.main()
