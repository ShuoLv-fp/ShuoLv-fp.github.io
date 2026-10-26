from pathlib import Path
import re
import unittest


class ProfilePublicationServiceUpdateTests(unittest.TestCase):
    def test_light_mode_is_the_default_and_dark_mode_remains_optional(self):
        script = Path("assets/js/dark-mode.js").read_text(encoding="utf-8")
        self.assertIn("const savedTheme = localStorage.getItem('theme');", script)
        self.assertIn("savedTheme === 'dark'", script)
        self.assertIn("localStorage.setItem('theme', 'light')", script)
        self.assertNotIn("localStorage.setItem('darkMode', null)", script)

    def test_publication_cards_use_responsive_three_to_seven_layout(self):
        styles = Path("assets/css/main.scss").read_text(encoding="utf-8")
        self.assertIn(".publication-card", styles)
        self.assertIn("grid-template-columns: minmax(0, 3fr) minmax(0, 7fr);", styles)
        self.assertRegex(
            styles,
            r"@media \(max-width: 700px\)[\s\S]*?grid-template-columns: minmax\(0, 1fr\);",
        )
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(7, text.count('class="publication-card"'))
                self.assertEqual(7, text.count('class="publication-card__figure"'))
                self.assertEqual(7, text.count('class="publication-card__details"'))
                self.assertNotIn("flex: 1 1 46%", text)

    def test_sidebar_profile_is_synchronized(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        for value in (
            'avatar           : "images/profile_202606.jpg"',
            'bio              : "Master Student in Electronic Information at Beijing Institute of Technology"',
            'bio_zh           : "北京理工大学电子信息硕士研究生"',
            'employer2        : "Xpertiise"',
            'employer2_zh     : "Xpertiise"',
        ):
            with self.subTest(value=value):
                self.assertIn(value, config)
        self.assertTrue(Path("images/profile_202606.jpg").is_file())

    def test_bilingual_academic_service_sections_are_in_matching_positions(self):
        expected = {
            Path("_pages/includes/academic_service.md"): (
                "Academic Service",
                "Reviewer",
            ),
            Path("_pages/includes/zh/academic_service.md"): (
                "社会兼职",
                "审稿人",
            ),
        }
        for path, labels in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for label in labels:
                    self.assertIn(label, text)
                self.assertIn("Nonlinear Dynamics", text)
                self.assertIn("Brain Structure and Function", text)

        page_pairs = (
            (Path("_pages/about.md"), "includes/academic_service.md"),
            (Path("_pages/zh.md"), "includes/zh/academic_service.md"),
        )
        for path, include in page_pairs:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(include, text)
                self.assertLess(text.index("honers.md"), text.index(include))
                self.assertLess(text.index(include), text.index("technical_skills.md"))

    def test_new_manuscript_is_not_publicly_linked(self):
        title = "Atypical functional hierarchy of the human cerebellum in autism"
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                card = text.split(title, 1)[0].rsplit('<div class="publication-card">', 1)[-1]
                card += title + text.split(title, 1)[1].split("</div>\n</div>", 1)[0]
                self.assertNotIn("atypical-functional-hierarchy-cerebellum-autism.pdf", card)
                self.assertNotRegex(card, rf'<a[^>]*>{re.escape(title)}</a>')
        self.assertFalse(
            Path("assets/files/atypical-functional-hierarchy-cerebellum-autism.pdf").exists()
        )


if __name__ == "__main__":
    unittest.main()
