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


if __name__ == "__main__":
    unittest.main()
