import unittest

from artifacts import ArtifactRegistry


class ArtifactRegistryTests(unittest.TestCase):
    def test_create_and_list(self):
        registry = ArtifactRegistry()
        artifact = registry.create("spec", "document")
        self.assertEqual(artifact["status"], "draft")
        self.assertEqual(registry.list()[0]["name"], "spec")


if __name__ == "__main__":
    unittest.main()
