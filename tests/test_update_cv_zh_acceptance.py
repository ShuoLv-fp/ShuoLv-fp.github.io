import unittest

from lxml import etree

from scripts.update_cv_zh_acceptance import FINAL_TITLE, update_document_xml


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


class ChineseCvOoxmlUpdateTests(unittest.TestCase):
    def test_updates_and_moves_publication_without_changing_authors(self):
        xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}"><w:body>
  <w:p><w:r><w:t>First-author paper one</w:t></w:r></w:p>
  <w:p><w:r><w:t>First-author paper two</w:t></w:r></w:p>
  <w:p><w:r><w:t>BrainLMM: fourth paper</w:t></w:r></w:p>
  <w:p>
    <w:r><w:t>Ruoqi Yang, Xinyu Wu, </w:t></w:r>
    <w:r><w:rPr><w:b/></w:rPr><w:t>Shuo Lv</w:t></w:r>
    <w:r><w:t>, … &amp; Guoyuan Yang*. </w:t></w:r>
    <w:r><w:t>Normative models of individualized functional brain networks reveal language network expansion in autism</w:t></w:r>
    <w:r><w:t>, Translational Psychiatry. </w:t></w:r>
    <w:r><w:t>（二轮审稿）</w:t></w:r>
  </w:p>
  <w:p><w:r><w:t>其中 1 篇一作 Nature Communications，1 篇在审</w:t></w:r></w:p>
</w:body></w:document>""".encode()

        updated = etree.fromstring(update_document_xml(xml))
        paragraphs = updated.xpath(".//w:p", namespaces=NS)
        texts = [
            "".join(p.xpath(".//w:t/text()", namespaces=NS))
            for p in paragraphs
        ]
        self.assertIn(FINAL_TITLE, texts[2])
        self.assertIn("BrainLMM: fourth paper", texts[3])
        self.assertIn(
            "Ruoqi Yang, Xinyu Wu, Shuo Lv, … & Guoyuan Yang*.",
            texts[2],
        )
        self.assertIn("Translational Psychiatry", texts[2])
        self.assertIn("2026 年 9 月接收", texts[2])
        self.assertNotIn("二轮审稿", " ".join(texts))
        self.assertIn(
            "1 篇被 Translational Psychiatry 接收",
            texts[-1],
        )

        paper = paragraphs[2]
        journal_runs = [
            run
            for run in paper.xpath("./w:r", namespaces=NS)
            if "Translational Psychiatry"
            in "".join(run.xpath(".//w:t/text()", namespaces=NS))
        ]
        self.assertEqual(1, len(journal_runs))
        self.assertTrue(
            journal_runs[0].xpath("./w:rPr/w:i", namespaces=NS)
        )
        shuo_runs = [
            run
            for run in paper.xpath("./w:r", namespaces=NS)
            if "Shuo Lv" in "".join(run.xpath(".//w:t/text()", namespaces=NS))
        ]
        self.assertTrue(shuo_runs[0].xpath("./w:rPr/w:b", namespaces=NS))


if __name__ == "__main__":
    unittest.main()
