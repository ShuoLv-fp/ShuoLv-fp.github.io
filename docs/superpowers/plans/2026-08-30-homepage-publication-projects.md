# Homepage Publication and Section Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CCSCW placeholder image, restore Markdown rendering in the two disclosure panels, and temporarily hide the requested homepage sections in both languages.

**Architecture:** Keep the existing Jekyll content structure and native disclosure widgets. Add one source-level regression test, make the smallest Kramdown/Liquid changes, and generate publication assets by deterministically rendering and cropping Fig. 2 from the supplied PDF.

**Tech Stack:** Jekyll 3.9, Kramdown GFM, Liquid, Python `unittest`, Poppler, Pillow

## Global Constraints

- Preserve the existing homepage visual style and all project/teaching wording.
- Keep English and Chinese homepage behavior synchronized.
- Preserve hidden hobby and collaborator source content.
- Use Fig. 2 from PDF page 4 and exclude the surrounding paper text and caption.

---

### Task 1: Add a failing homepage content regression test

**Files:**
- Create: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: English/Chinese homepage Markdown and include files.
- Produces: `HomepagePresentationTests`, a source-level regression suite used by later tasks.

- [ ] **Step 1: Write the failing test**

```python
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
            text = path.read_text(encoding="utf-8")
            self.assertIn('<details markdown="1">', text)

    def test_ccscw_card_uses_extracted_figure(self):
        for path in (
            Path("_pages/includes/pub.md"),
            Path("_pages/includes/zh/pub.md"),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn("/images/pub/pub_ccscw_sampling_detection.webp", text)
            self.assertNotIn("pub_ccscw_placeholder", text)
        for suffix in ("png", "webp"):
            self.assertTrue(Path(f"images/pub/pub_ccscw_sampling_detection.{suffix}").is_file())

    def test_hobbies_and_collaborators_are_liquid_commented(self):
        for path, passions_include, collaborators_heading in (
            (Path("_pages/about.md"), "includes/passions.md", "# 💡Collaborators and friends"),
            (Path("_pages/zh.md"), "includes/zh/passions.md", "# 💡合作者与朋友"),
        ):
            text = path.read_text(encoding="utf-8")
            comment_blocks = re.findall(
                r"{% comment %}(.*?){% endcomment %}", text, flags=re.DOTALL
            )
            self.assertTrue(
                any(
                    passions_include in block and collaborators_heading in block
                    for block in comment_blocks
                )
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_homepage_presentation.py -v`

Expected: FAIL because `markdown="1"`, the extracted image assets, new image references, and the Liquid comment block are absent.

- [ ] **Step 3: Commit the regression test**

```bash
git add tests/test_homepage_presentation.py
git commit -m "test: cover homepage presentation fixes"
```

### Task 2: Repair disclosure parsing and hide sections

**Files:**
- Modify: `_pages/includes/recent_projects.md:2`
- Modify: `_pages/includes/teaching.md:2`
- Modify: `_pages/includes/zh/recent_projects.md:2`
- Modify: `_pages/includes/zh/teaching.md:2`
- Modify: `_pages/about.md:45-49`
- Modify: `_pages/zh.md:42-46`

**Interfaces:**
- Consumes: Jekyll's Kramdown `markdown="1"` HTML-block extension and Liquid comments.
- Produces: correctly parsed disclosure contents and non-rendered hobby/collaborator sections.

- [ ] **Step 1: Enable Markdown inside all four disclosure panels**

Change each opening element from:

```html
<details>
```

to:

```html
<details markdown="1">
```

- [ ] **Step 2: Hide the two requested sections in both languages**

Wrap the existing passions include and collaborators heading/list together:

```liquid
{% comment %}
{% include_relative includes/passions.md %}

# 💡Collaborators and friends
- [Prof. Libo Zhang](https://scholar.google.com/citations?hl=zh-CN&user=8I-krtYAAAAJ) @ SWU.
{% endcomment %}
```

Use the equivalent existing Chinese include, heading, and list in `_pages/zh.md`.

- [ ] **Step 3: Run the focused tests**

Run: `python3 -m unittest tests/test_homepage_presentation.py -v`

Expected: disclosure and hiding tests PASS; image test still FAILS.

- [ ] **Step 4: Commit the section repairs**

```bash
git add _pages/about.md _pages/zh.md _pages/includes/recent_projects.md _pages/includes/teaching.md _pages/includes/zh/recent_projects.md _pages/includes/zh/teaching.md
git commit -m "fix: restore homepage section formatting"
```

### Task 3: Extract Fig. 2 and update the publication card

**Files:**
- Create: `images/pub/pub_ccscw_sampling_detection.png`
- Create: `images/pub/pub_ccscw_sampling_detection.webp`
- Modify: `_pages/includes/pub.md:70-74`
- Modify: `_pages/includes/zh/pub.md:70-74`

**Interfaces:**
- Consumes: page 4 of `978-981-92-0291-1_18.pdf` rendered at 300 DPI.
- Produces: matching PNG/WebP publication artwork referenced by both cards.

- [ ] **Step 1: Render the source page**

Run:

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -f 4 -l 4 -r 300 -png /Users/shuolv/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_luy0c8mxli2v12_cf1a/temp/drag/978-981-92-0291-1_18.pdf tmp/pdfs/ccscw/figure-page
```

Expected: `tmp/pdfs/ccscw/figure-page-04.png` at approximately 1831 x 2776 pixels.

- [ ] **Step 2: Crop and export the diagram**

Run the bundled Python/Pillow runtime to crop the Fig. 2 diagram from `(260, 1120, 1660, 1760)`, trim white borders, pad it with 24 white pixels, resize to at most 1400 pixels wide, and write both formats:

```python
from pathlib import Path
from PIL import Image, ImageChops

source = Image.open("tmp/pdfs/ccscw/figure-page-04.png").convert("RGB")
crop = source.crop((260, 1120, 1660, 1760))
white = Image.new("RGB", crop.size, "white")
bounds = ImageChops.difference(crop, white).getbbox()
if bounds is None:
    raise ValueError("Fig. 2 crop is blank")
diagram = crop.crop(bounds)
padded = Image.new("RGB", (diagram.width + 48, diagram.height + 48), "white")
padded.paste(diagram, (24, 24))
if padded.width > 1400:
    height = round(padded.height * 1400 / padded.width)
    padded = padded.resize((1400, height), Image.Resampling.LANCZOS)
output = Path("images/pub/pub_ccscw_sampling_detection")
padded.save(output.with_suffix(".png"), optimize=True)
padded.save(output.with_suffix(".webp"), quality=88, method=6)
```

- [ ] **Step 3: Inspect the crop and adjust only if it clips diagram content**

Open `images/pub/pub_ccscw_sampling_detection.png` and confirm the detection arrows, both network layers, and the right-side state labels are present, with no body text or caption.

- [ ] **Step 4: Update both publication cards**

Replace every `/images/pub/pub_ccscw_placeholder.webp` reference with `/images/pub/pub_ccscw_sampling_detection.webp`, and remove the obsolete comments that describe replacing the placeholder later in the English and Chinese publication includes.

- [ ] **Step 5: Run all source tests**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 6: Build and visually verify the site**

Run: `bundle exec jekyll build`

Expected: exit code 0. Serve `_site`, inspect `/` and `/zh/` with both disclosure panels expanded, and confirm there is no raw Markdown and the new image appears correctly.

- [ ] **Step 7: Commit the publication image update**

```bash
git add images/pub/pub_ccscw_sampling_detection.png images/pub/pub_ccscw_sampling_detection.webp _pages/includes/pub.md _pages/includes/zh/pub.md
git commit -m "feat: add CCSCW publication figure"
```
