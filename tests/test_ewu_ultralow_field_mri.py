from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "_pages" / "ewu-ultralow-field-mri.html"
STYLE = ROOT / "assets" / "css" / "ewu-ultralow-field-mri.scss"
SCRIPT = ROOT / "assets" / "js" / "ewu-ultralow-field-mri.js"
IMAGE_DIR = ROOT / "images" / "ewu-ultralow-field-mri"


EXPECTED_DOIS = {
    "10.1038/s41467-021-27317-1",
    "10.1002/mrm.29642",
    "10.1126/sciadv.adi9327",
    "10.1038/s41597-023-02181-4",
    "10.1038/s44222-023-00086-w",
    "10.1002/nbm.4956",
    "10.1002/mrm.30046",
    "10.1126/science.adm7168",
    "10.1002/nbm.5213",
    "10.1002/mrm.30231",
    "10.1002/ctm2.70071",
    "10.1002/nbm.5268",
    "10.1109/tmi.2025.3597401",
    "10.1109/tbme.2025.3580111",
    "10.1109/tbme.2026.3656493",
    "10.1161/strokeaha.126.052978",
    "10.1002/nbm.70373",
    "10.1002/mrm.70583",
}


EXPECTED_IMAGES = {
    "whole-body-system.jpg",
    "whole-body-contrasts.jpg",
    "fast-brain-pipeline.jpg",
    "clinical-case-comparison.jpg",
    "emi-pipeline.jpg",
    "emi-comparison.jpg",
}


class EwuUltraLowFieldMriReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_page_is_a_chinese_jekyll_route_with_scoped_assets(self):
        self.assertIn("permalink: /research/ewu-ultralow-field-mri/", self.html)
        self.assertIn("lang: zh", self.html)
        self.assertIn("/assets/css/ewu-ultralow-field-mri.css", self.html)
        self.assertIn("/assets/js/ewu-ultralow-field-mri.js", self.html)
        self.assertTrue(STYLE.is_file())
        self.assertTrue(SCRIPT.is_file())

    def test_all_eighteen_peer_reviewed_articles_are_present_once(self):
        dois = {
            value.lower()
            for value in re.findall(r'data-doi="([^"]+)"', self.html)
        }
        self.assertEqual(EXPECTED_DOIS, dois)
        self.assertEqual(18, len(re.findall(r'<article class="paper-card"', self.html)))

    def test_research_tracks_and_progressive_disclosure_exist(self):
        for track in ("platform", "ai", "emi", "protocol", "review"):
            with self.subTest(track=track):
                self.assertRegex(self.html, rf'data-filter="{track}"')
        self.assertEqual(18, len(re.findall(r'<details class="paper-details"', self.html)))
        self.assertIn('id="paper-count" aria-live="polite"', self.html)
        self.assertIn('aria-pressed="true"', self.html)

    def test_personal_research_lens_is_explicit_and_cautious(self):
        self.assertIn('id="personal-lens"', self.html)
        for phrase in (
            "人脑动力学与个体差异",
            "BrainLMM 与基础模型",
            "规范模型与临床泛化",
            "AI Agent 与科研工作流",
            "研究推演，不是吴老师团队的既有结论",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.html)

    def test_important_figures_are_local_attributed_and_accessible(self):
        referenced = set(
            re.findall(r'/images/ewu-ultralow-field-mri/([^"?]+)', self.html)
        )
        self.assertEqual(EXPECTED_IMAGES, referenced)
        for image_name in EXPECTED_IMAGES:
            with self.subTest(image=image_name):
                self.assertTrue((IMAGE_DIR / image_name).is_file())
        self.assertEqual(6, len(re.findall(r'<figure class="evidence-figure"', self.html)))
        self.assertNotRegex(self.html, r'<img(?![^>]*\balt="[^"]+")[^>]*>')
        self.assertEqual(6, self.html.count("图源：BISP Lab / The University of Hong Kong"))

    def test_external_links_use_safe_new_tabs(self):
        links = re.findall(r'<a\s+[^>]*target="_blank"[^>]*>', self.html)
        self.assertGreater(len(links), 18)
        for link in links:
            with self.subTest(link=link):
                self.assertIn('rel="noopener noreferrer"', link)

    def test_filter_script_is_local_and_progressive(self):
        self.assertNotIn("fetch(", self.script)
        self.assertIn("aria-pressed", self.script)
        self.assertIn("paper.hidden", self.script)
        self.assertIn("URLSearchParams", self.script)


if __name__ == "__main__":
    unittest.main()
