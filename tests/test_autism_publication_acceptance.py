from pathlib import Path
import unittest


FINAL_TITLE = (
    "Alterations in functional brain network topography in autism "
    "revealed by normative models"
)
OLD_TITLE = (
    "Normative models of individualized functional brain networks "
    "reveal language network expansion in autism"
)
PREPRINT_URL = "https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1"
IMAGE = "/images/pub/pub_biorxiv_autism.webp"
AUTHORS = (
    '<span class="pub-coauthor">Ruoqi Yang</span>, '
    '<span class="pub-coauthor">Xinyu Wu</span>, <strong>Shuo Lv</strong>, '
    '<span class="pub-coauthor">Jinlong Li</span>, '
    '<span class="pub-coauthor">Zhiming Wang</span>, '
    '<span class="pub-coauthor">Wenjing Zhu</span>, '
    '<span class="pub-coauthor">Tan Gao</span>, '
    '<span class="pub-coauthor">Guoyuan Yang*</span>'
)


class AutismPublicationHomepageTests(unittest.TestCase):
    def test_bilingual_cards_use_final_metadata_and_preserve_assets(self):
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(FINAL_TITLE, text)
                self.assertIn("Translational Psychiatry", text)
                self.assertIn(PREPRINT_URL, text)
                self.assertEqual(2, text.count(IMAGE))
                self.assertIn(AUTHORS, text)
                self.assertNotIn(OLD_TITLE, text)

    def test_publication_is_third_after_two_first_author_papers(self):
        ordered_titles = (
            "Three parsimonious spatiotemporal patterns in cerebellum",
            "Effects of experts on the coupling dynamics",
            FINAL_TITLE,
            "Development of areal-level individualized homologous",
        )
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for title in ordered_titles:
                    self.assertIn(title, text)
                positions = [text.find(title) for title in ordered_titles]
                self.assertEqual(sorted(positions), positions)

    def test_related_homepage_copy_reports_acceptance(self):
        expected = {
            Path("_pages/includes/research_interests.md"): (
                "alterations in functional brain network topography in autism",
                "accepted by *Translational Psychiatry* in Sep. 2026",
            ),
            Path("_pages/includes/zh/research_interests.md"): (
                "自闭症功能脑网络拓扑的异常改变",
                "*Translational Psychiatry* 于 2026 年 9 月接收",
            ),
            Path("_pages/includes/recent_projects.md"): (
                "accepted by *Translational Psychiatry*",
            ),
            Path("_pages/includes/zh/recent_projects.md"): (
                "*Translational Psychiatry* 接收",
            ),
        }
        for path, phrases in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for phrase in phrases:
                    self.assertIn(phrase, text)
                self.assertNotIn("under review", text.lower())
                self.assertNotIn("审稿", text)

    def test_news_files_are_not_rewritten_with_the_acceptance(self):
        for path in (
            Path("_pages/includes/news.md"),
            Path("_pages/includes/zh/news.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(FINAL_TITLE, text)
                self.assertNotIn("Translational Psychiatry", text)


if __name__ == "__main__":
    unittest.main()
