from pathlib import Path
import unittest

from pypdf import PdfReader


SOURCE_PATH = Path("assets/files/cv_en.tex")
PDF_PATH = Path("assets/files/CV202609_EN.pdf")


class EnglishCvSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")

    def test_compact_one_page_layout_contract(self):
        self.assertIn("left=0.45in,right=0.45in", self.source)
        self.assertIn("top=0.35in,bottom=0.35in", self.source)
        self.assertNotIn(r"\newpage", self.source)

    def test_linked_header_without_phone_or_birth_date(self):
        required = (
            "mailto:lv_shuo@foxmail.com",
            "https://www.google.com/maps/place/Beijing",
            "https://ShuoLv-fp.github.io",
            "https://github.com/ShuoLv-fp",
            "https://scholar.google.com/citations?user=VAsm0T8AAAAJ",
            "https://orcid.org/0009-0009-2540-0485",
            r"\faEnvelope",
            r"\faMapMarkerAlt",
            r"\faGlobe",
            r"\faGithub",
            r"\faGraduationCap",
            r"\faOrcid",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.source)
        self.assertNotIn("CVPhone", self.source)
        self.assertNotIn("Born Mar. 2002", self.source)

    def test_education_and_roles(self):
        required = (
            "M.Eng. in Electronic Information (Biomedical Engineering)",
            "Sep. 2024 -- Present",
            "B.Eng. in Data Science and Big Data Technology",
            "Sep. 2020 -- Jun. 2024",
            "Beijing, China",
            "Chongqing, China",
            r"Ranked \textbf{2/103}",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.source)
        for removed in ("085409", "080910T", "Research interests:", "Project Lead"):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, self.source)
        self.assertEqual(4, self.source.count("{Lead Researcher}"))
        self.assertEqual(1, self.source.count("{Lead Developer}"))
        self.assertEqual(1, self.source.count("{Researcher}"))

    def test_sections_and_publications_are_preserved(self):
        self.assertIn(r"\section{Research Internship}", self.source)
        self.assertIn(r"\section{Research Experience}", self.source)
        self.assertEqual(6, self.source.count(r"\cvpublication" + "{"))
        self.assertEqual(7, self.source.count(r"\experienceentry" + "{"))
        self.assertNotIn(r"\url{", self.source)
        targets = (
            "https://doi.org/10.1038/s41467-026-72931-6",
            "https://doi.org/10.1007/s11071-023-09146-7",
            "https://doi.org/10.1609/aaai.v40i6.42413",
            "https://link.springer.com/book/10.1007/978-981-92-0291-1",
            "https://doi.org/10.1038/s42003-025-08509-7",
            "https://doi.org/10.1101/2025.10.23.684286",
        )
        for target in targets:
            with self.subTest(target=target):
                self.assertIn(target, self.source)


class EnglishCvPdfTests(unittest.TestCase):
    def test_pdf_is_one_a4_page_with_expected_links(self):
        reader = PdfReader(PDF_PATH)
        self.assertEqual(1, len(reader.pages))
        page = reader.pages[0]
        self.assertAlmostEqual(595.28, float(page.mediabox.width), delta=1.0)
        self.assertAlmostEqual(841.89, float(page.mediabox.height), delta=1.0)

        uris = set()
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                uris.add(str(action["/URI"]))
        expected = {
            "mailto:lv_shuo@foxmail.com",
            "https://www.google.com/maps/place/Beijing",
            "https://ShuoLv-fp.github.io",
            "https://github.com/ShuoLv-fp",
            "https://scholar.google.com/citations?user=VAsm0T8AAAAJ",
            "https://orcid.org/0009-0009-2540-0485",
            "https://doi.org/10.1038/s41467-026-72931-6",
            "https://doi.org/10.1007/s11071-023-09146-7",
            "https://doi.org/10.1609/aaai.v40i6.42413",
            "https://link.springer.com/book/10.1007/978-981-92-0291-1",
            "https://doi.org/10.1038/s42003-025-08509-7",
            "https://doi.org/10.1101/2025.10.23.684286",
        }
        self.assertTrue(expected.issubset(uris), expected - uris)

        text = page.extract_text()
        for section in (
            "EDUCATION",
            "SELECTED PUBLICATIONS",
            "RESEARCH INTERNSHIP",
            "RESEARCH EXPERIENCE",
            "AWARDS AND HONORS",
            "TECHNICAL SKILLS",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text.upper())
        self.assertNotIn("Born Mar. 2002", text)
        self.assertNotIn("+86 133", text)


if __name__ == "__main__":
    unittest.main()

