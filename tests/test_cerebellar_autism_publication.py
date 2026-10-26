from pathlib import Path
import unittest


TITLE = "Atypical functional hierarchy of the human cerebellum in autism"
PRECEDING_TITLE = (
    "Alterations in functional brain network topography in autism "
    "revealed by normative models"
)
FOLLOWING_TITLE = (
    "Development of areal-level individualized homologous functional "
    "parcellations in youth"
)
PAPER = "/assets/files/atypical-functional-hierarchy-cerebellum-autism.pdf"
IMAGE = "/images/pub/pub_cerebellar_autism_gradient.webp"
CODE = "https://github.com/BIT-YangLab/ASD-Cerebellar-Functional-Gradients"
AUTHORS = (
    '<span class="pub-coauthor">Wenjing Zhu</span>, '
    '<span class="pub-coauthor">Yu Zhang</span>, '
    '<span class="pub-coauthor">Ruoqi Yang</span>, '
    '<strong>Shuo Lv</strong>, '
    '<span class="pub-coauthor">Tan Gao</span>, '
    '<span class="pub-coauthor">Xinyu Wu</span>, '
    '<span class="pub-coauthor">Tiantian Liu</span>, '
    '<span class="pub-coauthor">Chuyang Ye</span>, '
    '<span class="pub-coauthor">Guoyuan Yang*</span>, '
    '<span class="pub-coauthor">Tianyi Yan*</span>'
)


class CerebellarAutismPublicationTests(unittest.TestCase):
    def test_bilingual_cards_include_metadata_and_links(self):
        expected_status = {
            Path("_pages/includes/pub.md"): "under review, Sep 2026",
            Path("_pages/includes/zh/pub.md"): "在投，2026 年 9 月",
        }

        for path, status in expected_status.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(TITLE, text)
                self.assertIn(AUTHORS, text)
                self.assertIn(status, text)
                self.assertEqual(2, text.count(PAPER))
                self.assertEqual(2, text.count(IMAGE))
                self.assertIn(CODE, text)

    def test_card_has_requested_position(self):
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                positions = [
                    text.find(PRECEDING_TITLE),
                    text.find(TITLE),
                    text.find(FOLLOWING_TITLE),
                ]
                self.assertTrue(all(position >= 0 for position in positions))
                self.assertEqual(sorted(positions), positions)

    def test_static_assets_exist(self):
        for path in (
            Path("assets/files/atypical-functional-hierarchy-cerebellum-autism.pdf"),
            Path("images/pub/pub_cerebellar_autism_gradient.png"),
            Path("images/pub/pub_cerebellar_autism_gradient.webp"),
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
