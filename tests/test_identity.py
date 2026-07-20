import unittest

import identity

EXPECTED_TREE = "/\n└── Ω∞v Compiler\n    └── OceanicOS\n        └── Living Agnostic Charter"


class IdentityTests(unittest.TestCase):
    def test_render_is_the_exact_lineage_tree(self):
        self.assertEqual(identity.render(), EXPECTED_TREE)

    def test_as_list_is_the_four_names_root_first(self):
        self.assertEqual(
            identity.as_list(),
            ["/", "Ω∞v Compiler", "OceanicOS", "Living Agnostic Charter"],
        )

    def test_every_level_has_a_gloss(self):
        for name, gloss in identity.TREE:
            self.assertTrue(name)
            self.assertTrue(gloss.strip())


if __name__ == "__main__":
    unittest.main()
