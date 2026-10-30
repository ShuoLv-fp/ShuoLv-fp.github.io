from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


class ProfilePublicationServiceUpdateTests(unittest.TestCase):
    @staticmethod
    def visible_source(text):
        text = re.sub(r"\{%\s*comment\s*%\}[\s\S]*?\{%\s*endcomment\s*%\}", "", text)
        return re.sub(r"<!--[\s\S]*?-->", "", text)

    def test_light_mode_is_the_default_and_dark_mode_remains_optional(self):
        script = Path("assets/js/dark-mode.js").read_text(encoding="utf-8")
        self.assertIn("const savedTheme = localStorage.getItem('theme');", script)
        self.assertIn("savedTheme === 'dark'", script)
        self.assertIn("localStorage.setItem('theme', 'light')", script)
        self.assertNotIn("localStorage.setItem('darkMode', null)", script)

    def test_publication_cards_use_responsive_two_to_eight_layout(self):
        styles = Path("assets/css/main.scss").read_text(encoding="utf-8")
        self.assertIn(".publication-card", styles)
        self.assertIn(
            "grid-template-columns: minmax(0, 20%) minmax(0, 80%);",
            styles,
        )
        self.assertIn("padding-left: 24px;", styles)
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
                self.assertEqual(7, text.count('class="pub-highlight"'))
                self.assertNotIn(
                    'class="pub-highlight"',
                    self.visible_source(text),
                )

    def test_internships_match_the_education_row_geometry(self):
        styles = Path("assets/css/main.scss").read_text(encoding="utf-8")
        logo_rule = re.search(
            r"\.experience-row__logo\s*\{(?P<body>.*?)\}",
            styles,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(logo_rule)
        for declaration in (
            "width: 60px;",
            "height: 60px;",
            "margin-left: 50px;",
            "margin-right: 50px;",
            "border-radius: 0;",
            "object-fit: contain;",
        ):
            self.assertIn(declaration, logo_rule.group("body"))

        for path in (
            Path("_pages/includes/recent_projects.md"),
            Path("_pages/includes/zh/recent_projects.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(
                    2,
                    text.count('<img class="experience-row__logo"'),
                )
                self.assertNotIn('<div class="experience-row__logo">', text)

    def test_bytedance_symbol_has_transparent_canvas_padding(self):
        root = ET.parse(
            "_pages/includes/images/bytedance.svg"
        ).getroot()
        self.assertEqual("60", root.attrib["width"])
        self.assertEqual("60", root.attrib["height"])
        self.assertEqual("-3.5 8 35.5 31.5", root.attrib["viewBox"])

    def test_research_outcomes_are_commented_and_ai4science_is_concise(self):
        expected = {
            Path("_pages/includes/research_interests.md"): (
                "Key outcomes",
                "I am interested in using LLM-based agents",
            ),
            Path("_pages/includes/zh/research_interests.md"): (
                "代表性成果",
                "我关注利用大语言模型智能体",
            ),
        }
        for path, (outcome_label, ai_copy) in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                visible = self.visible_source(text)
                self.assertIn(outcome_label, text)
                self.assertNotIn(outcome_label, visible)
                self.assertIn(ai_copy, visible)
                self.assertNotIn("ByteDance", visible)
                self.assertNotIn("字节跳动", visible)

    def test_technical_toolkit_shows_only_two_categories(self):
        expected = {
            Path("_pages/includes/technical_skills.md"): (
                ("Programming", "Neuroimaging &amp; research"),
                ("Machine learning", "Agents &amp; language models"),
            ),
            Path("_pages/includes/zh/technical_skills.md"): (
                ("编程语言", "神经影像与科研"),
                ("机器学习", "智能体与大语言模型"),
            ),
        }
        for path, (visible_labels, hidden_labels) in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                visible = self.visible_source(text)
                for label in visible_labels:
                    self.assertIn(label, visible)
                for label in hidden_labels:
                    self.assertIn(label, text)
                    self.assertNotIn(label, visible)

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
