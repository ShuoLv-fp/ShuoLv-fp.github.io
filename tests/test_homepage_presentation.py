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

    def test_skills_exploration_text_and_focus_contrast(self):
        stylesheet = Path("_sass/_skills.scss").read_text(encoding="utf-8")

        def declarations(selector):
            match = re.search(
                rf"(?m)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}",
                stylesheet,
            )
            self.assertIsNotNone(match, selector)
            return dict(
                re.findall(r"([\w-]+)\s*:\s*([^;]+);", match.group(1))
            )

        def luminance(hex_color):
            channels = [
                int(hex_color[index : index + 2], 16) / 255
                for index in (1, 3, 5)
            ]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return sum(weight * channel for weight, channel in zip(
                (0.2126, 0.7152, 0.0722), linear
            ))

        def contrast(first, second):
            lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
            return (lighter + 0.05) / (darker + 0.05)

        light = declarations(".skills-profile")
        dark = declarations('[data-theme="dark"] .skills-profile')
        kicker = declarations(".skills-kicker--exploring")
        dark_kicker = declarations('[data-theme="dark"] .skills-kicker--exploring')
        focus = declarations(".technical-toolkit a:focus-visible")
        marker = declarations(".exploration-card::before")

        self.assertEqual(light["--skills-coral"].lower(), "#d95d4f")
        self.assertEqual(marker["background"], "var(--skills-coral)")
        self.assertEqual(kicker["color"], "var(--skills-coral-text)")
        self.assertEqual(dark_kicker["color"], "var(--skills-coral-text)")
        self.assertEqual(focus["outline"], "3px solid var(--skills-focus)")

        for theme, variables, surface in (
            ("light", light, "#ffffff"),
            ("dark", {**light, **dark}, "#242a31"),
        ):
            with self.subTest(theme=theme):
                self.assertGreaterEqual(
                    contrast(variables["--skills-coral-text"], surface), 4.5
                )
                self.assertGreaterEqual(
                    contrast(variables["--skills-focus"], surface), 3.0
                )


if __name__ == "__main__":
    unittest.main()
