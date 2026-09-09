from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PaperFeedPageTests(unittest.TestCase):
    def test_bilingual_routes_and_navigation_exist(self):
        self.assertIn("permalink: /paper-feed/", (ROOT / "_pages/paper-feed.md").read_text())
        self.assertIn("permalink: /zh/paper-feed/", (ROOT / "_pages/paper-feed-zh.md").read_text())
        self.assertIn("Paper Feed", (ROOT / "_data/navigation.yml").read_text())
        self.assertIn("学术速递", (ROOT / "_data/navigation-zh.yml").read_text())

    def test_feed_styles_include_responsive_dark_focus_and_print_states(self):
        css = (ROOT / "_sass/_paper-feed.scss").read_text()
        for marker in (
            ".paper-feed-card",
            "[data-theme=\"dark\"]",
            "@media (max-width: 48rem)",
            ":focus-visible",
            "@media print",
        ):
            self.assertIn(marker, css)

    def test_renderer_does_not_inject_untrusted_html(self):
        script = (ROOT / "assets/js/paper-feed.js").read_text()
        self.assertNotIn("innerHTML =", script)
        self.assertIn("textContent", script)

    def test_feed_has_one_page_heading_and_coherent_dynamic_heading_levels(self):
        include = (ROOT / "_includes/paper-feed.html").read_text()
        script = (ROOT / "assets/js/paper-feed.js").read_text()
        self.assertEqual(include.count("<h1"), 1)
        self.assertIn('element(document, "h2", "paper-feed__date"', script)
        self.assertIn('element(document, "h3", "paper-feed-card__title"', script)
        self.assertIn('element(document, "h4", "paper-feed-card__label"', script)

    def test_feed_styles_are_loaded_after_dark_mode(self):
        main = (ROOT / "assets/css/main.scss").read_text()
        self.assertGreater(main.index('@import "paper-feed"'), main.index('@import "dark-mode"'))

    def test_superpowers_scratch_directory_is_ignored(self):
        ignored = (ROOT / ".gitignore").read_text().splitlines()
        self.assertIn(".superpowers/", ignored)


if __name__ == "__main__":
    unittest.main()
