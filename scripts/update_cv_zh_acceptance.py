from pathlib import Path
import shutil
import sys
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}
OLD_TITLE = (
    "Normative models of individualized functional brain networks "
    "reveal language network expansion in autism"
)
FINAL_TITLE = (
    "Alterations in functional brain network topography in autism "
    "revealed by normative models"
)
OLD_OUTPUT = "其中 1 篇一作 Nature Communications，1 篇在审"
NEW_OUTPUT = (
    "其中 1 篇一作 Nature Communications，"
    "1 篇被 Translational Psychiatry 接收"
)


def node_text(node):
    return "".join(node.xpath(".//w:t/text()", namespaces=NS))


def set_run_text(run, value):
    texts = run.xpath(".//w:t", namespaces=NS)
    if not texts:
        raise ValueError("target run has no text node")
    texts[0].text = value
    if value[:1].isspace() or value[-1:].isspace():
        texts[0].set(f"{{{XML}}}space", "preserve")
    for extra in texts[1:]:
        extra.getparent().remove(extra)


def set_italic(run):
    rpr = run.find(f"{{{W}}}rPr")
    if rpr is None:
        rpr = etree.Element(f"{{{W}}}rPr")
        run.insert(0, rpr)
    if rpr.find(f"{{{W}}}i") is None:
        rpr.append(etree.Element(f"{{{W}}}i"))


def update_document_xml(xml_bytes):
    root = etree.fromstring(xml_bytes)
    paragraphs = root.xpath(".//w:p", namespaces=NS)
    paper = next(p for p in paragraphs if OLD_TITLE in node_text(p))
    brainlmm = next(p for p in paragraphs if "BrainLMM:" in node_text(p))
    runs = paper.xpath("./w:r|./w:hyperlink/w:r", namespaces=NS)
    title_index = next(
        i for i, run in enumerate(runs) if OLD_TITLE in node_text(run)
    )

    set_run_text(runs[title_index], FINAL_TITLE)
    set_run_text(runs[title_index + 1], ", Translational Psychiatry. ")
    set_italic(runs[title_index + 1])
    set_run_text(runs[title_index + 2], "（2026 年 9 月接收）")
    brainlmm.addprevious(paper)

    output = next(p for p in paragraphs if OLD_OUTPUT in node_text(p))
    output_run = next(
        run
        for run in output.xpath("./w:r|./w:hyperlink/w:r", namespaces=NS)
        if OLD_OUTPUT in node_text(run)
    )
    set_run_text(output_run, NEW_OUTPUT)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
    )


def update_docx(source, destination):
    with NamedTemporaryFile(suffix=".docx", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        with ZipFile(source) as source_zip, ZipFile(
            temp_path, "w", ZIP_DEFLATED
        ) as destination_zip:
            for item in source_zip.infolist():
                data = source_zip.read(item.filename)
                if item.filename == "word/document.xml":
                    data = update_document_xml(data)
                destination_zip.writestr(item, data)
        shutil.move(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: update_cv_zh_acceptance.py INPUT.docx OUTPUT.docx"
        )
    update_docx(Path(sys.argv[1]), Path(sys.argv[2]))
