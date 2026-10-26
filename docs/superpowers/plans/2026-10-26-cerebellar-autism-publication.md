# Cerebellar Autism Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the September 2026 under-review cerebellar autism manuscript to the bilingual homepage publication list with a Figure 1 thumbnail and hosted PDF.

**Architecture:** Follow the existing static Jekyll publication-card pattern. Store the supplied paper and extracted Figure 1 as static assets, reference them from both language includes, and protect exact metadata and ordering with a source-level acceptance test.

**Tech Stack:** Jekyll, Markdown/HTML includes, Python `unittest`, Poppler/Pillow image tooling.

## Global Constraints

- Preserve all existing uncommitted edits, including the English Translational Psychiatry metadata change.
- Insert the new card immediately after the autism network-topography paper and before the IHFP paper.
- Use `under review, Sep 2026` in English and `在投，2026 年 9 月` in Chinese.
- Use Figure 1 and the supplied manuscript PDF; do not claim a journal, DOI, acceptance, or impact factor.

---

### Task 1: Add publication acceptance coverage

**Files:**
- Create: `tests/test_cerebellar_autism_publication.py`

**Interfaces:**
- Consumes: the publication includes and expected static-asset paths.
- Produces: regression assertions for bilingual metadata, ordering, links, and assets.

- [ ] **Step 1: Write a failing `unittest` covering the title, complete author line, under-review status, September 2026 date, code link, asset references, and exact placement in both language files.**
- [ ] **Step 2: Run `python3 -m unittest tests.test_cerebellar_autism_publication -v`; expect failures because the card and assets are absent.**
- [ ] **Step 3: Keep the failing test unchanged while implementing Tasks 2 and 3.**

### Task 2: Add the manuscript and Figure 1 assets

**Files:**
- Create: `assets/files/atypical-functional-hierarchy-cerebellum-autism.pdf`
- Create: `images/pub/pub_cerebellar_autism_gradient.png`
- Create: `images/pub/pub_cerebellar_autism_gradient.webp`

**Interfaces:**
- Consumes: the supplied 29-page manuscript and its Figure 1 on page 23.
- Produces: stable site-relative paper and image URLs used by both publication cards.

- [ ] **Step 1: Copy the source PDF to the stable site asset path.**
- [ ] **Step 2: Extract the embedded Figure 1 image from PDF page 23 and save a lossless PNG.**
- [ ] **Step 3: Convert the PNG to WebP with visually lossless settings and verify dimensions and nonzero file sizes.**

### Task 3: Add synchronized bilingual publication cards

**Files:**
- Modify: `_pages/includes/pub.md`
- Modify: `_pages/includes/zh/pub.md`

**Interfaces:**
- Consumes: `/assets/files/atypical-functional-hierarchy-cerebellum-autism.pdf`, `/images/pub/pub_cerebellar_autism_gradient.webp`, and the GitHub code URL.
- Produces: one publication card in each homepage language.

- [ ] **Step 1: Insert the English card after the Translational Psychiatry card with the exact authors, `under review, Sep 2026`, paper and code links, and a concise hierarchy-focused highlight.**
- [ ] **Step 2: Insert the Chinese card at the identical position with `在投，2026 年 9 月`, localized link labels, and equivalent Chinese highlight copy.**
- [ ] **Step 3: Run the focused acceptance test and require all assertions to pass.**

### Task 4: Verify the complete site

**Files:**
- Verify: generated `_site/index.html` and `_site/zh/index.html`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified bilingual static pages with working local asset references.

- [ ] **Step 1: Run `python3 -m unittest discover -s tests -v` and require zero failures.**
- [ ] **Step 2: Run `bundle exec jekyll build` and require exit code 0.**
- [ ] **Step 3: inspect the generated HTML for ordering, English/Chinese status text, paper/code URLs, and image URLs.**
- [ ] **Step 4: visually inspect the final Figure 1 crop for legibility and absence of page furniture.**
