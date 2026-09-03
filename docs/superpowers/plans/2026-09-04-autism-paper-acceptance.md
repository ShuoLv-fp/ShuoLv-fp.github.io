# Autism Paper Acceptance Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the accepted autism paper consistently across both CVs and the bilingual homepage while preserving its authors, preprint link, homepage image, and third-place ordering.

**Architecture:** Treat the user-confirmed publication metadata as the single source of truth and protect it with regression tests before changing content. Apply small text edits to Markdown and LaTeX, use a deterministic OOXML helper for the existing Chinese Word source, then regenerate and visually inspect both PDFs. News files remain outside the implementation scope and are explicitly checked for accidental changes.

**Tech Stack:** Jekyll Markdown/Liquid, Python `unittest` and `pypdf`, LaTeX/Tectonic, DOCX OOXML (`zipfile` + `lxml`), LibreOffice/Poppler rendering.

## Global Constraints

- Final title: **Alterations in functional brain network topography in autism revealed by normative models**
- Journal: *Translational Psychiatry*
- Status: accepted in September 2026; the final article is not yet online.
- Keep the bioRxiv preprint link: `https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1` on the homepage and the existing bioRxiv DOI link in the English CV.
- Do not add DOI, volume, issue, article number, or pages for the accepted journal version.
- Preserve the exact current author order and `/images/pub/pub_biorxiv_autism.webp`.
- Place the publication third, after the two independent first-author papers.
- Do not modify `_pages/includes/news.md` or `_pages/includes/zh/news.md`.
- Preserve the English CV as one A4 page and the Chinese CV as two A4 pages.
- Run each required artifact marker successfully exactly once, immediately before its first authoring command.

---

### Task 1: Add publication metadata and ordering regression tests

**Files:**
- Create: `tests/test_autism_publication_acceptance.py`
- Modify: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: current homepage fragments, English LaTeX source, and generated PDF paths.
- Produces: regression checks used by every later task.

- [ ] **Step 1: Write the failing bilingual homepage tests**

Create `tests/test_autism_publication_acceptance.py`:

```python
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
                positions = [text.index(title) for title in ordered_titles]
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
```

- [ ] **Step 2: Extend English CV tests with metadata, order, and bilingual PDF checks**

In `tests/test_cv_en_document.py`, add `ZH_PDF_PATH = Path("assets/files/CV202609_ZH.pdf")`. Add this method to `EnglishCvSourceTests`:

```python
    def test_accepted_autism_paper_metadata_and_order(self):
        final_title = (
            "Alterations in functional brain network topography in autism "
            "revealed by normative models"
        )
        ordered_titles = (
            "Three parsimonious spatiotemporal patterns in cerebellum",
            "Effects of experts on the coupling dynamics",
            final_title,
            "BrainLMM: A Label-Free Framework",
        )
        positions = [self.source.index(title) for title in ordered_titles]
        self.assertEqual(sorted(positions), positions)
        self.assertIn(
            r"\textit{Transl Psychiatry} (accepted Sep. 2026)",
            self.source,
        )
        self.assertIn(
            "https://doi.org/10.1101/2025.10.23.684286",
            self.source,
        )
        self.assertNotIn(
            "Normative models of individualized functional brain networks "
            "reveal language network expansion in autism",
            self.source,
        )
```

Add this class before the final `unittest.main()` block:

```python
class AcceptedPaperPdfTests(unittest.TestCase):
    def test_generated_pdfs_contain_accepted_paper(self):
        final_title = (
            "Alterations in functional brain network topography in autism "
            "revealed by normative models"
        )
        for path, page_count in ((PDF_PATH, 1), (ZH_PDF_PATH, 2)):
            with self.subTest(path=path):
                reader = PdfReader(path)
                self.assertEqual(page_count, len(reader.pages))
                text = " ".join(
                    "\n".join(
                        page.extract_text() or "" for page in reader.pages
                    ).split()
                )
                self.assertIn(final_title, text)
                self.assertIn("Translational Psychiatry", text)
```

- [ ] **Step 3: Run focused tests and verify the new assertions fail**

Run:

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -p 'test_autism_publication_acceptance.py' -v
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_cv_en_document.py -v
```

Expected: failures for the final title, accepted status, and third-place CV ordering.

- [ ] **Step 4: Commit the failing tests**

```bash
git add tests/test_autism_publication_acceptance.py tests/test_cv_en_document.py
git commit -m "test: define accepted autism paper metadata"
```

---

### Task 2: Update the bilingual homepage outside News

**Files:**
- Modify: `_pages/includes/pub.md`
- Modify: `_pages/includes/zh/pub.md`
- Modify: `_pages/includes/research_interests.md`
- Modify: `_pages/includes/zh/research_interests.md`
- Modify: `_pages/includes/recent_projects.md`
- Modify: `_pages/includes/zh/recent_projects.md`
- Test: `tests/test_autism_publication_acceptance.py`

**Interfaces:**
- Consumes: metadata constants and ordering contract from Task 1.
- Produces: matching English and Chinese homepage content for the accepted paper.

- [ ] **Step 1: Update the English publication card in place**

Keep the card third and preserve its author line, image path, preprint links, and code link. Replace the title, image `alt`, status, and highlight with:

```html
alt="Alterations in functional brain network topography in autism"
```

```html
<span style="font-weight: 600; font-size: 1.05em;"><a href="https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1" target="_blank">Alterations in functional brain network topography in autism revealed by normative models</a></span><br>
```

```html
<em>Translational Psychiatry</em>, accepted Sep 2026 &nbsp;|&nbsp; <a href="https://github.com/BIT-YangLab/NormativeModels_TopologicalNetwork_Autism" target="_blank">[Code]</a>
<div class="pub-highlight">Uses normative models to reveal alterations in functional brain network topography in autism.</div>
```

- [ ] **Step 2: Update the Chinese publication card in place**

Keep the same preserved elements and use:

```html
alt="Alterations in functional brain network topography in autism"
```

```html
<span style="font-weight: 600; font-size: 1.05em;"><a href="https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1" target="_blank">Alterations in functional brain network topography in autism revealed by normative models</a></span><br>
```

```html
<em>Translational Psychiatry</em>，2026 年 9 月接收 &nbsp;|&nbsp; <a href="https://github.com/BIT-YangLab/NormativeModels_TopologicalNetwork_Autism" target="_blank">[代码]</a>
<div class="pub-highlight">通过规范模型揭示自闭症功能脑网络拓扑的异常改变。</div>
```

- [ ] **Step 3: Update related homepage summaries**

Use these exact replacements:

```markdown
- Normative modeling reveals alterations in functional brain network topography in autism (accepted by *Translational Psychiatry* in Sep. 2026).
```

```markdown
- 通过规范模型揭示自闭症功能脑网络拓扑的异常改变（*Translational Psychiatry* 于 2026 年 9 月接收）。
```

```markdown
- **Output:** 2 articles, including a first-author article in *Nature Communications* and one accepted by *Translational Psychiatry*.
```

```markdown
- **成果：** 相关论文 2 篇，包括 1 篇一作 *Nature Communications* 论文和 1 篇被 *Translational Psychiatry* 接收的论文。
```

- [ ] **Step 4: Run homepage tests**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -p 'test_autism_publication_acceptance.py' -v
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_homepage_presentation.py tests/test_cv_projects_update.py -v
```

Expected: all homepage-related tests pass.

- [ ] **Step 5: Confirm News is absent from the diff and commit**

```bash
git diff --name-only | rg '(^|/)news\.md$'
git add _pages/includes/pub.md _pages/includes/zh/pub.md _pages/includes/research_interests.md _pages/includes/zh/research_interests.md _pages/includes/recent_projects.md _pages/includes/zh/recent_projects.md
git commit -m "docs: mark autism paper accepted"
```

Expected: the first command prints nothing; the commit contains only the six named files.

---

### Task 3: Update and regenerate the one-page English CV

**Files:**
- Modify: `assets/files/cv_en.tex`
- Modify: `assets/files/CV202609_EN.pdf`
- Test: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: metadata and ordering tests from Task 1.
- Produces: a one-page linked English PDF and its LaTeX source.

- [ ] **Step 1: Move and rewrite the accepted-paper LaTeX entry**

Move the entry to immediately after *Nonlinear Dynamics* and use:

```tex
  \cvpublication{Yang, R., Wu, X., \textbf{Lv, S.} \textit{et al.}}
    {Alterations in functional brain network topography in autism revealed by normative models}
    {\textit{Transl Psychiatry} (accepted Sep. 2026).}
    {https://doi.org/10.1101/2025.10.23.684286}
```

Delete its former sixth-position copy so the publication count remains six.

- [ ] **Step 2: Update the related research-experience sentence**

Replace the end of the Low-Dimensional Spatiotemporal Dynamics entry with:

```tex
resulting in \textbf{2 articles}: a first-author \textit{Nature Communications} article and one accepted by \textit{Translational Psychiatry}.
```

- [ ] **Step 3: Run the English source tests**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_cv_en_document.py -v
```

Expected: source assertions pass; generated-PDF assertions still fail because the PDFs are not regenerated yet.

- [ ] **Step 4: Mark PDF authoring exactly once**

From `/Users/shuolv/.codex/plugins/cache/openai-primary-runtime/pdf/26.826.12353/skills/pdf`, run:

```bash
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 2 --output-format pdf
```

Expected: successful marker confirmation. Do not run this marker again during the implementation.

- [ ] **Step 5: Compile twice with the verified Tectonic 0.17.0 binary**

```bash
/tmp/codex-tectonic-0.17.0-fast/tectonic -X compile assets/files/cv_en.tex --outdir assets/files --keep-logs
/tmp/codex-tectonic-0.17.0-fast/tectonic -X compile assets/files/cv_en.tex --outdir assets/files --keep-logs
```

Expected: `assets/files/CV202609_EN.pdf` is regenerated as one A4 page with stable links and no overflow warnings.

- [ ] **Step 6: Run English PDF tests and commit**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_cv_en_document.py -v
git add assets/files/cv_en.tex assets/files/CV202609_EN.pdf
git commit -m "docs: update accepted paper in English CV"
```

Expected: English source/PDF assertions pass; the Chinese accepted-paper assertion remains pending Task 4.

---

### Task 4: Update the Chinese Word source and regenerate its PDF

**Files:**
- Create: `scripts/update_cv_zh_acceptance.py`
- Modify: `/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.docx`
- Modify: `assets/files/CV202609_ZH.pdf`
- Test: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: the matching two-page Word source and metadata tests from Task 1.
- Produces: an updated editable Word source and a two-page repository PDF.

- [ ] **Step 1: Create a deterministic OOXML updater**

Create `scripts/update_cv_zh_acceptance.py`:

```python
from pathlib import Path
import shutil
import sys
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
OLD_TITLE = (
    "Normative models of individualized functional brain networks "
    "reveal language network expansion in autism"
)
FINAL_TITLE = (
    "Alterations in functional brain network topography in autism "
    "revealed by normative models"
)


def node_text(node):
    return "".join(node.xpath(".//w:t/text()", namespaces=NS))


def set_run_text(run, value):
    texts = run.xpath(".//w:t", namespaces=NS)
    texts[0].text = value
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
    title_index = next(i for i, run in enumerate(runs) if OLD_TITLE in node_text(run))
    set_run_text(runs[title_index], FINAL_TITLE)
    set_run_text(runs[title_index + 1], ", Translational Psychiatry. ")
    set_italic(runs[title_index + 1])
    set_run_text(runs[title_index + 2], "（2026 年 9 月接收）")
    brainlmm.addprevious(paper)

    output = next(
        p for p in paragraphs
        if "其中 1 篇一作 Nature Communications，1 篇在审" in node_text(p)
    )
    output_run = next(
        run for run in output.xpath("./w:r|./w:hyperlink/w:r", namespaces=NS)
        if "其中 1 篇一作 Nature Communications，1 篇在审" in node_text(run)
    )
    set_run_text(
        output_run,
        "其中 1 篇一作 Nature Communications，"
        "1 篇被 Translational Psychiatry 接收",
    )
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
    )


def update_docx(source, destination):
    with ZipFile(source) as zin, NamedTemporaryFile(suffix=".docx", delete=False) as temp:
        temp_path = Path(temp.name)
    with ZipFile(source) as zin, ZipFile(temp_path, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = update_document_xml(data)
            zout.writestr(item, data)
    shutil.move(temp_path, destination)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: update_cv_zh_acceptance.py INPUT.docx OUTPUT.docx")
    update_docx(Path(sys.argv[1]), Path(sys.argv[2]))
```

- [ ] **Step 2: Mark DOCX authoring exactly once**

From `/Users/shuolv/.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents`, run:

```bash
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format docx
```

Expected: successful marker confirmation. Do not run this marker again during the implementation.

- [ ] **Step 3: Generate a candidate DOCX without overwriting the source**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/update_cv_zh_acceptance.py "/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.docx" "/private/tmp/202609北京理工大学-吕硕-个人简历-接收更新.docx"
```

Expected: the candidate contains the final title as the third publication and reports acceptance in the related research output.

- [ ] **Step 4: Render the candidate DOCX and retain its PDF**

The PDF marker has already run in Task 3; do not repeat it.

```bash
env TMPDIR=/private/tmp /Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/shuolv/.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/render_docx.py "/private/tmp/202609北京理工大学-吕硕-个人简历-接收更新.docx" --output_dir /private/tmp/cv_zh_acceptance_render --emit_pdf
```

Expected: `page-1.png`, `page-2.png`, and `202609北京理工大学-吕硕-个人简历-接收更新.pdf` exist; no third page exists.

- [ ] **Step 5: Inspect both rendered Chinese pages at full resolution**

Open `/private/tmp/cv_zh_acceptance_render/page-1.png` and `page-2.png`. Confirm that the longer title does not overlap adjacent entries, the acceptance status remains legible, the publication is third, and all unrelated sections retain their previous layout.

Expected: both pages are visually clean. If the affected publication wraps poorly, change only that paragraph's spacing or font size in the OOXML updater, rerender, and reinspect.

- [ ] **Step 6: Promote the verified candidate and keep a backup**

```bash
cp "/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.docx" "/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-接收前备份.docx"
cp "/private/tmp/202609北京理工大学-吕硕-个人简历-接收更新.docx" "/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.docx"
cp "/private/tmp/cv_zh_acceptance_render/202609北京理工大学-吕硕-个人简历-接收更新.pdf" assets/files/CV202609_ZH.pdf
```

Expected: the verified source becomes the editable master, the previous source remains recoverable, and the repository PDF is two pages.

- [ ] **Step 7: Run bilingual PDF tests and commit**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_cv_en_document.py -v
git add scripts/update_cv_zh_acceptance.py assets/files/CV202609_ZH.pdf
git commit -m "docs: update accepted paper in Chinese CV"
```

Expected: all English and Chinese CV tests pass.

---

### Task 5: Full verification and visual QA

**Files:**
- Verify: `assets/files/CV202609_EN.pdf`
- Verify: `assets/files/CV202609_ZH.pdf`
- Verify: bilingual homepage sources

**Interfaces:**
- Consumes: all deliverables from Tasks 1-4.
- Produces: final evidence that content, layout, links, build output, and scope are correct.

- [ ] **Step 1: Run the complete test suite and site build**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -v
bundle exec jekyll build
```

Expected: all tests pass and Jekyll exits successfully with no Liquid or Markdown errors.

- [ ] **Step 2: Render and inspect the English PDF**

```bash
mkdir -p /private/tmp/cv_en_acceptance_render
pdftoppm -png -r 150 assets/files/CV202609_EN.pdf /private/tmp/cv_en_acceptance_render/page
```

Open `/private/tmp/cv_en_acceptance_render/page-1.png` at full resolution. Confirm one clean page, no clipped text, and readable publication spacing.

- [ ] **Step 3: Verify geometry, page counts, links, and exact text**

```bash
pdfinfo assets/files/CV202609_EN.pdf
pdfinfo assets/files/CV202609_ZH.pdf
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests/test_cv_en_document.py -v
```

Expected: English is one A4 page, Chinese is two A4 pages, the English PDF retains the preprint link, and both PDFs contain the final title and journal.

- [ ] **Step 4: Confirm scope and inspect the final commit range**

```bash
git status --short
git diff --name-only HEAD~4..HEAD | rg '(^|/)news\.md$'
git diff --check
git log --oneline --max-count=6
git diff --stat HEAD~4..HEAD
```

Expected: no News path, no unexpected uncommitted files, no whitespace errors, and four focused implementation commits after the specification and plan commits.

