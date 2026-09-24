from pathlib import Path
import re
import unittest


class HomepagePresentationTests(unittest.TestCase):
    def test_markdown_is_enabled_in_disclosure_panels(self):
        for path in (
            Path("_pages/includes/recent_projects.md"),
            Path("_pages/includes/teaching.md"),
            Path("_pages/includes/zh/recent_projects.md"),
            Path("_pages/includes/zh/teaching.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn('<details markdown="1">', text)

    def test_ccscw_card_uses_extracted_figure(self):
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(
                    "/images/pub/pub_ccscw_sampling_detection.webp", text
                )
                self.assertNotIn("pub_ccscw_placeholder", text)

        for suffix in ("png", "webp"):
            with self.subTest(suffix=suffix):
                self.assertTrue(
                    Path(
                        f"images/pub/pub_ccscw_sampling_detection.{suffix}"
                    ).is_file()
                )

    def test_hobbies_and_collaborators_are_liquid_commented(self):
        for path, passions_include, collaborators_heading in (
            (
                Path("_pages/about.md"),
                "includes/passions.md",
                "# 💡Collaborators and friends",
            ),
            (
                Path("_pages/zh.md"),
                "includes/zh/passions.md",
                "# 💡合作者与朋友",
            ),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                comment_blocks = re.findall(
                    r"{% comment %}(.*?){% endcomment %}",
                    text,
                    flags=re.DOTALL,
                )
                self.assertTrue(
                    any(
                        passions_include in block
                        and collaborators_heading in block
                        for block in comment_blocks
                    )
                )

    def test_skills_sections_use_evidence_driven_structure(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn('class="skills-profile"', text)
                self.assertIn('class="skills-capabilities"', text)
                self.assertEqual(text.count('class="capability-card"'), 3)
                self.assertIn('class="exploration-grid"', text)
                self.assertEqual(text.count('class="exploration-card"'), 3)
                self.assertIn('class="technical-toolkit"', text)

    def test_skills_sections_connect_claims_to_evidence(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count('class="evidence-row"'), 3)
                self.assertGreaterEqual(text.count('class="evidence-link"'), 6)
                self.assertIn('href="#publications"', text)
                self.assertIn('href="#projects"', text)

    def test_skills_sections_use_text_statuses_without_level_bars(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count('class="capability-status"'), 6)
                self.assertNotIn("skill-bar", text)
                self.assertNotIn("aria-valuenow", text)

    def test_skills_content_is_localized(self):
        english = Path("_pages/includes/technical_skills.md").read_text(
            encoding="utf-8"
        )
        chinese = Path("_pages/includes/zh/technical_skills.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Demonstrated capabilities", english)
        self.assertIn("Computational Neuroscience &amp; Neuroimaging", english)
        self.assertIn("Exploring next", english)
        self.assertIn("Technical toolkit", english)

        self.assertIn("已验证的能力", chinese)
        self.assertIn("计算神经科学与神经影像", chinese)
        self.assertIn("正在探索", chinese)
        self.assertIn("技术工具箱", chinese)

    def test_skills_stylesheet_is_imported(self):
        entrypoint = Path("assets/css/main.scss").read_text(encoding="utf-8")
        partial = Path("_sass/_skills.scss")

        self.assertIn('@import "skills";', entrypoint)
        self.assertTrue(partial.is_file())


if __name__ == "__main__":
    unittest.main()
