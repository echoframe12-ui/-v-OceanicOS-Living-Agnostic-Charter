import unittest

from plugins import PluginRegistry


class PluginRegistryTests(unittest.TestCase):
    def test_register_and_list(self):
        registry = PluginRegistry()
        plugin = registry.register("github", ["tool", "sync"])
        self.assertEqual(plugin["name"], "github")
        self.assertEqual(registry.list()[0]["capabilities"], ["tool", "sync"])


if __name__ == "__main__":
    unittest.main()
