# One-Page English CV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a polished, clickable, one-page English academic CV and replace the PDF currently linked from the homepage.

**Architecture:** Keep the CV as one self-contained LaTeX source and add a focused Python regression test that checks both the source contract and generated PDF. Use Tectonic 0.17.0 only as a temporary local build tool, then validate structurally with pypdf/Poppler and visually from a rendered PNG.

**Tech Stack:** LaTeX, Tectonic 0.17.0, Python 3 `unittest`, pypdf, Poppler, Git

## Global Constraints

- Output must be exactly one A4 page.
- Keep `Research Internship` and `Research Experience` separate.
- Keep all six publications, the ByteDance internship, six research projects, five awards, and all skill categories.
- Use `M.Eng. in Electronic Information (Biomedical Engineering)` and `B.Eng. in Data Science and Big Data Technology`; omit discipline codes, visible GPA/course placeholders, BIT research interests, telephone number, and birth date.
- Use clickable icons for email, location, homepage, GitHub, Google Scholar, and ORCID.
- Use linked publication titles without visible DOI/URL strings.
- Preserve the portrait assets and unrelated website content.
- Do not use bare repository-wide `pytest` as an acceptance gate: without root collection configuration it currently collects generated `_site` tests and an independent private application whose imports are not initialized. Run only the explicit tests below.

---

## File Structure

- `assets/files/cv_en.tex`: editable English CV source, including layout macros and content.
- `assets/files/CV202609_EN.pdf`: generated one-page artifact already referenced by `_config.yml`.
- `tests/test_cv_en_document.py`: source and PDF regression checks.

### Task 1: Add the CV regression contract

**Files:**
- Create: `tests/test_cv_en_document.py`
- Test: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: UTF-8 LaTeX source and the generated PDF.
- Produces: acceptance checks for Tasks 2–3.

- [ ] **Step 1: Write the failing test**

Create `tests/test_cv_en_document.py`:

```python
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
            r"\faEnvelope", r"\faMapMarkerAlt", r"\faGlobe",
            r"\faGithub", r"\faGraduationCap", r"\faOrcid",
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
            "Beijing, China", "Chongqing, China",
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
            "EDUCATION", "SELECTED PUBLICATIONS", "RESEARCH INTERNSHIP",
            "RESEARCH EXPERIENCE", "AWARDS AND HONORS", "TECHNICAL SKILLS",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text.upper())
        self.assertNotIn("Born Mar. 2002", text)
        self.assertNotIn("+86 133", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify the source tests fail for the existing layout**

Run:

```bash
python3 -m pytest tests/test_cv_en_document.py::EnglishCvSourceTests -q
```

Expected: failures for margins, header, education, publication macros, and role labels.

### Task 2: Rewrite the source into the approved structure

**Files:**
- Modify: `assets/files/cv_en.tex`
- Test: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: current factual CV content and Task 1 tests.
- Produces: XeLaTeX-compatible source with `\educationentry`, `\cvpublication`, and `\experienceentry`.

- [ ] **Step 1: Implement the compact page and header**

Use:

```latex
\documentclass[a4paper,10pt]{article}
\usepackage[a4paper,top=0.35in,bottom=0.35in,left=0.45in,right=0.45in]{geometry}
\usepackage{newtxtext,newtxmath,xcolor,enumitem,tabularx,titlesec,hyperref,microtype,array,fontawesome5}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{0pt}
\linespread{0.98}
\titleformat{\section}{\normalsize\scshape\bfseries}{}{0pt}{}[\vspace{0.02em}\titlerule]
\titlespacing*{\section}{0pt}{0.34em}{0.22em}
\newcommand{\contactlink}[3]{\href{#1}{\textcolor{accent}{#2}\,\textcolor{black}{#3}}}
\newcommand{\cvpublication}[4]{\item #1 \href{#4}{\textcolor{accent}{#2}}. #3}
```

The header retains the name and existing research keywords. Its `\footnotesize` contact row uses these six linked label/icon pairs: Email/`\faEnvelope`, Beijing, China/`\faMapMarkerAlt`, Homepage/`\faGlobe`, GitHub/`\faGithub`, Scholar/`\faGraduationCap`, and ORCID/`\faOrcid`. Use the exact six URLs from Task 1 and no phone or birth date.

- [ ] **Step 2: Implement education in the reference layout**

Define a two-line `\educationentry{institution}{location}{degree}{dates}{detail}` macro. Use:

```latex
\educationentry{Beijing Institute of Technology}{Beijing, China}
  {M.Eng. in Electronic Information (Biomedical Engineering)}
  {Sep. 2024 -- Present}{}
% Optional fields intentionally omitted until confirmed:
% GPA: ; Courses:

\educationentry{Southwest University}{Chongqing, China}
  {B.Eng. in Data Science and Big Data Technology}
  {Sep. 2020 -- Jun. 2024}
  {Ranked \textbf{2/103}; received the \textbf{National Scholarship twice}, the Gratitude to Modern Chinese Scientists Scholarship, and the Top-Tier Scholarship.}
% Optional fields intentionally omitted until confirmed:
% GPA: ; Courses:
```

- [ ] **Step 3: Link all six publication titles**

Keep author order, venue, volume, pages/article number, and year. Put each title in accent color and link the title itself to its canonical target from Task 1. Use exactly six `\cvpublication{authors}{title}{venue details}{canonical URL}` calls and remove every visible `\url{...}`.

- [ ] **Step 4: Convert each experience to one paragraph**

Define `\experienceentry{title}{role}{dates}{advisor}{paragraph}`. Keep the sections separate and use these exact entries:

```text
ByteDance, Seed Foundation Model - AI4Math | Research Intern, AI Agent Development
General-Purpose Cybersecurity Agent | Lead Researcher
Low-Dimensional Spatiotemporal Dynamics of the Human Brain | Lead Researcher
Complex Social Awareness Modeling | Lead Researcher
Intelligent Factory Security | Lead Researcher
Large Language Model for Early Childhood Education | Researcher
Xiangqi Game-Playing System | Lead Developer
```

Preserve all current dates and advisors. ByteDance retains `5 iterations`, `100+ problems`, `6.4/7`, `600+`, `70%+`, `2,000+`, and `11`. Cybersecurity retains `5 specialized agents`, `16-node bounded state machine`, `R0--R3`, `Finding--Evidence`, human approval, and the two-layer blackboard. The brain project retains complex PCA, three dominant patterns, sCCA/SVM associations, and two manuscripts. Keep the substantive descriptions for the other projects, but omit prize repetition because Awards lists those results.

- [ ] **Step 5: Tighten awards and skills**

Keep every current row. Set both tables to `\footnotesize` and `\renewcommand{\arraystretch}{0.94}`; use award columns `0.105\textwidth`, flexible `X`, and `0.20\textwidth`.

- [ ] **Step 6: Run source tests and commit**

Run:

```bash
python3 -m pytest tests/test_cv_en_document.py::EnglishCvSourceTests -q
git diff --check
git add assets/files/cv_en.tex tests/test_cv_en_document.py
git commit -m "feat: redesign English CV for one-page layout"
```

Expected: source tests pass; diff check is silent; source and tests are committed.

### Task 3: Build and validate the PDF

**Files:**
- Modify: `assets/files/CV202609_EN.pdf`
- Test: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: Task 2 LaTeX source.
- Produces: one A4 PDF with twelve expected link targets.

- [ ] **Step 1: Install a pinned temporary compiler**

Run:

```bash
mkdir -p /tmp/codex-tectonic-0.17.0
/usr/bin/curl -L --fail --silent --show-error \
  https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-aarch64-apple-darwin.tar.gz \
  -o /tmp/codex-tectonic-0.17.0/tectonic.tar.gz
tar -xzf /tmp/codex-tectonic-0.17.0/tectonic.tar.gz -C /tmp/codex-tectonic-0.17.0
/tmp/codex-tectonic-0.17.0/tectonic --version
```

Expected: Tectonic 0.17.0.

- [ ] **Step 2: Mark the PDF edit operation exactly once**

From `/Users/shuolv/.codex/plugins/cache/openai-primary-runtime/pdf/26.826.12353/skills/pdf`, run exactly once:

```bash
node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format pdf
```

- [ ] **Step 3: Compile in an isolated directory**

Run:

```bash
mkdir -p tmp/cv-en-build
/tmp/codex-tectonic-0.17.0/tectonic -o tmp/cv-en-build assets/files/cv_en.tex
pdfinfo tmp/cv-en-build/cv_en.pdf | rg '^(Pages|Page size):'
```

Expected: `Pages: 1` and A4 `595.276 x 841.89 pts`. If the first build is longer than one page, keep margins/content and reduce, in order: experience after-space to `0.16em`; publication item separation to `0.10em`; section spacing to `0.28em`/`0.18em`; body type to `8.7pt` with `9.6pt` leading. Do not go below `8.5pt`, drop content, or merge the sections.

- [ ] **Step 4: Promote and test the artifact**

Run:

```bash
cp tmp/cv-en-build/cv_en.pdf assets/files/CV202609_EN.pdf
python3 -m pytest tests/test_cv_en_document.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Render and visually inspect**

Run:

```bash
mkdir -p tmp/cv-en-final
pdftoppm -png -r 160 -f 1 -singlefile assets/files/CV202609_EN.pdf tmp/cv-en-final/page
```

Inspect `tmp/cv-en-final/page.png` at original detail. Confirm no clipping/overlap, aligned icons and dates, six visible section headings, and readable smallest text.

- [ ] **Step 6: Commit the artifact**

Run:

```bash
git add assets/files/cv_en.tex assets/files/CV202609_EN.pdf tests/test_cv_en_document.py
git commit -m "docs: publish September 2026 English CV"
```

### Task 4: Final verification and push

**Files:**
- Verify: `assets/files/cv_en.tex`
- Verify: `assets/files/CV202609_EN.pdf`
- Verify: `_config.yml`
- Verify: `tests/test_cv_en_document.py`

**Interfaces:**
- Consumes: committed source and PDF.
- Produces: pushed `main` branch.

- [ ] **Step 1: Run focused checks**

Run:

```bash
python3 -m pytest tests/test_cv_en_document.py -q
python3 -m pytest tests/test_cv_projects_update.py -q -k 'not profile_uses_new_portrait_and_preserves_original'
pdfinfo assets/files/CV202609_EN.pdf | rg '^(Pages|Page size):'
rg -n 'cv_en\s+: "assets/files/CV202609_EN\.pdf"' _config.yml
git diff --check HEAD^
```

Expected: CV tests pass; five relevant homepage/project tests pass; PDF is one A4 page; config points to it; diff check is silent. The excluded portrait assertion is pre-existing and stale: it expects a `.jpg`, while commit `34a4216` and the tracked asset use `.png`.

- [ ] **Step 2: Check scope**

Run:

```bash
git status --short
git log -3 --oneline
git diff --stat 34a4216..HEAD
```

Expected: only render output may remain under `tmp/`; committed changes are the design, plan, LaTeX source, generated PDF, and focused test.

- [ ] **Step 3: Push**

Run:

```bash
git push origin main
```

Expected: remote `main` advances to the final CV commit.
