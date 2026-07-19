import unittest

from nodes import STRIPPED_ATTRIBUTES, NodeRegistry


class NodeRegistryTests(unittest.TestCase):
    def test_mount_strips_to_agnostic_form(self):
        registry = NodeRegistry()
        node = registry.mount("/Nigeria")
        self.assertEqual(node["name"], "nigeria")
        self.assertEqual(node["mount"], "/nigeria")
        self.assertEqual(node["flux"], "high")
        self.assertTrue(node["agnostic"])
        self.assertEqual(node["stripped"], STRIPPED_ATTRIBUTES)

    def test_stripping_is_uniform_for_every_node(self):
        registry = NodeRegistry()
        first = registry.mount("alpha")
        second = registry.mount("omega")
        self.assertEqual(first["stripped"], second["stripped"])

    def test_remount_replaces_and_list_returns_all(self):
        registry = NodeRegistry()
        registry.mount("alpha")
        registry.mount("alpha", flux="low")
        registry.mount("omega")
        nodes = registry.list()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]["flux"], "low")

    def test_empty_name_raises(self):
        registry = NodeRegistry()
        with self.assertRaises(ValueError):
            registry.mount("  / ")


if __name__ == "__main__":
    unittest.main()
