import unittest

import badge


class CviColorTests(unittest.TestCase):
    def test_at_or_above_threshold_is_green(self):
        self.assertEqual(badge.cvi_color(0.74), "#3fb950")
        self.assertEqual(badge.cvi_color(0.9), "#3fb950")
        self.assertEqual(badge.cvi_color(1.0), "#3fb950")

    def test_bands_step_down_below_threshold(self):
        self.assertEqual(badge.cvi_color(0.73), "#d29922")  # yellow near-miss
        self.assertEqual(badge.cvi_color(0.6), "#d29922")
        self.assertEqual(badge.cvi_color(0.5), "#db6d28")  # orange
        self.assertEqual(badge.cvi_color(0.4), "#db6d28")
        self.assertEqual(badge.cvi_color(0.39), "#f85149")  # red
        self.assertEqual(badge.cvi_color(0.0), "#f85149")

    def test_out_of_range_clamps(self):
        self.assertEqual(badge.cvi_color(2.0), "#3fb950")
        self.assertEqual(badge.cvi_color(-1.0), "#f85149")

    def test_non_numeric_is_grey(self):
        self.assertEqual(badge.cvi_color(None), "#8b949e")
        self.assertEqual(badge.cvi_color("x"), "#8b949e")
        self.assertEqual(badge.cvi_color(float("nan")), "#8b949e")


class RenderTests(unittest.TestCase):
    def test_render_is_svg_with_both_cells(self):
        svg = badge.render("verification", "0.82", "#3fb950")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))
        self.assertIn("verification", svg)
        self.assertIn("0.82", svg)
        self.assertIn("#3fb950", svg)

    def test_accessible_label_present(self):
        svg = badge.render("verification", "0.82", "#3fb950")
        self.assertIn('aria-label="verification: 0.82"', svg)
        self.assertIn("<title>verification: 0.82</title>", svg)

    def test_message_text_is_escaped(self):
        svg = badge.render("l", "<script>&\"", "#000")
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)
        self.assertIn("&amp;", svg)

    def test_width_grows_with_text(self):
        short = badge.render("v", "0.8", "#000")
        long = badge.render("verification index", "0.80", "#000")
        sw = int(short.split('width="', 1)[1].split('"', 1)[0])
        lw = int(long.split('width="', 1)[1].split('"', 1)[0])
        self.assertGreater(lw, sw)

    def test_content_type_is_svg(self):
        self.assertEqual(badge.CONTENT_TYPE, "image/svg+xml")


if __name__ == "__main__":
    unittest.main()
