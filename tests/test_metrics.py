import unittest

import metrics


class MetricsRenderTests(unittest.TestCase):
    def test_render_emits_help_type_and_sample(self):
        text = metrics.render(
            [{"name": "oceanicos_cvi", "help": "the index", "value": 0.8}]
        )
        self.assertIn("# HELP oceanicos_cvi the index", text)
        self.assertIn("# TYPE oceanicos_cvi gauge", text)
        self.assertIn("oceanicos_cvi 0.8", text)
        self.assertTrue(text.endswith("\n"))

    def test_booleans_render_as_one_or_zero(self):
        text = metrics.render(
            [
                {"name": "up", "help": "h", "value": True},
                {"name": "down", "help": "h", "value": False},
            ]
        )
        self.assertIn("\nup 1", text)
        self.assertIn("\ndown 0", text)

    def test_type_defaults_to_gauge_and_can_be_overridden(self):
        text = metrics.render(
            [{"name": "n", "help": "h", "value": 1, "type": "counter"}]
        )
        self.assertIn("# TYPE n counter", text)

    def test_integers_render_without_decimals(self):
        text = metrics.render([{"name": "n", "help": "h", "value": 42}])
        self.assertIn("n 42\n", text)


if __name__ == "__main__":
    unittest.main()
