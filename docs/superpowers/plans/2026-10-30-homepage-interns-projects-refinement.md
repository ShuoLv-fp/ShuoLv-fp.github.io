# Homepage Interns and Projects Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the bilingual publication and research sections, promote internships and projects to a visible first-level section, and reduce the technical toolkit to two visible categories.

**Architecture:** Preserve the existing Jekyll include structure and anchors. Use HTML/Liquid comments for retained hidden copy, shared CSS classes for the Education-matched internship rows, and local image assets for company logos.

**Tech Stack:** Jekyll, Markdown with embedded HTML/Liquid, SCSS, Python `unittest`/`pytest`.

## Global Constraints

- Every visible content and layout change must be synchronized in English and Chinese.
- Existing hidden content must be commented out, not deleted.
- Human Intelligence must show `Details forthcoming` / `详情待补充` without invented facts.
- ByteDance must appear once under internships and not remain duplicated under projects.
- Keep `#projects`, `#publications`, and `#research` anchors stable.
- Company logos must be local, proportionally scaled, lazy-loaded, and have meaningful alt text.

---

### Task 1: Add Regression Tests for the New Information Architecture

**Files:**
- Modify: `tests/test_profile_publication_service_update.py`
- Modify: `tests/test_cv_projects_update.py`

**Interfaces:**
- Consumes: existing bilingual Markdown includes and `assets/css/main.scss`
- Produces: assertions for 2:8 publication layout, hidden summaries/outcomes/toolkit rows, visible internships/projects, and local logos

- [ ] **Step 1: Replace the 3:7 assertion with 2:8 and assert contribution summaries are retained only in comments**

Add assertions for `grid-template-columns: minmax(0, 2fr) minmax(0, 8fr);`, seven commented `.pub-highlight` blocks in each language, and no visible `.pub-highlight` block after comments are stripped.

- [ ] **Step 2: Add bilingual research/toolkit assertions**

Assert ByteDance is absent from the visible AI4Science paragraph, Key outcomes lists remain inside comments, and only Programming plus Neuroimaging & research remain visible after comments are stripped.

- [ ] **Step 3: Replace the old seven-project structure test**

Assert each file has a first-level `Interns and Projects` / `实习与项目` heading, no `<details>`, internship before projects, ByteDance before Human Intelligence, six project entries in their existing order, local logo paths, and bilingual placeholder copy.

- [ ] **Step 4: Run focused tests and verify they fail**

Run: `python3 -m pytest tests/test_profile_publication_service_update.py tests/test_cv_projects_update.py -q`

Expected: failures for the old 3:7 ratio, collapsed project block, visible summaries/outcomes/toolkit rows, and missing internship rows/logos.

### Task 2: Simplify Publications, Research Interests, and Toolkit

**Files:**
- Modify: `assets/css/main.scss`
- Modify: `_pages/includes/pub.md`
- Modify: `_pages/includes/zh/pub.md`
- Modify: `_pages/includes/research_interests.md`
- Modify: `_pages/includes/zh/research_interests.md`
- Modify: `_pages/includes/technical_skills.md`
- Modify: `_pages/includes/zh/technical_skills.md`

**Interfaces:**
- Consumes: existing `.publication-card` and toolkit markup
- Produces: 2:8 desktop publication grid and bilingual source-commented optional content

- [ ] **Step 1: Change the publication grid to 2:8**

Change only the desktop `grid-template-columns`; preserve the 700px single-column rule and text styles.

- [ ] **Step 2: Comment all publication contribution summaries**

Wrap each complete `.pub-highlight` element in `{% comment %}` / `{% endcomment %}` so the text remains in source but is absent from generated HTML.

- [ ] **Step 3: Comment research outcomes and shorten AI4Science**

Wrap each Key outcomes label and list in Liquid comments. Use concise bilingual copy about LLM agents accelerating scientific discovery, automating workflows, and supporting verifiable reasoning, with no ByteDance reference.

- [ ] **Step 4: Comment two toolkit rows per language**

Wrap Machine learning and Agents & language models rows in HTML comments while keeping Programming and Neuroimaging & research visible.

- [ ] **Step 5: Run the focused content tests**

Run: `python3 -m pytest tests/test_profile_publication_service_update.py -q`

Expected: all publication, research, and toolkit assertions pass; internship assertions may still fail until Task 3.

### Task 3: Build the Visible Interns and Projects Section

**Files:**
- Modify: `_pages/includes/recent_projects.md`
- Modify: `_pages/includes/zh/recent_projects.md`
- Modify: `assets/css/main.scss`
- Create: `_pages/includes/images/bytedance.svg` or an equivalent verified local raster asset
- Create: `_pages/includes/images/human-intelligence.*`

**Interfaces:**
- Consumes: ByteDance dates and accomplishments from `assets/files/cv_en.tex` and existing project copy
- Produces: stable `#projects` section with `.experience-row`, `.experience-row__logo`, and `.experience-row__details` markup

- [ ] **Step 1: Obtain and validate official/public company logos**

Use official company/public brand sources. Store compact local assets under `_pages/includes/images/`, inspect their dimensions/content, and record the source URLs in source comments near the markup or the plan notes.

- [ ] **Step 2: Replace the collapsed wrapper with first-level headings**

Use `# 🚀 Interns and Projects` / `# 🚀 实习与项目`, followed by `## Intern Experience` / `## 实习经历`, then `## Projects` / `## 项目经历`. Preserve `<span class='anchor' id='projects'></span>`.

- [ ] **Step 3: Add the two Education-style internship rows**

ByteDance shows Nov. 2025-May 2026, a verified location if available, `Research Intern, AI Agent Development`, and concise existing accomplishments. Human Intelligence shows only company name plus `Details forthcoming` / `详情待补充`.

- [ ] **Step 4: Keep the six non-ByteDance projects**

Preserve their existing order and copy. Remove the former ByteDance project entry to avoid duplication.

- [ ] **Step 5: Add responsive experience-row CSS**

Match Education's 60px visual-logo treatment on desktop, use proportional `object-fit: contain`, and reduce spacing/stack cleanly below 700px.

- [ ] **Step 6: Run both focused test files**

Run: `python3 -m pytest tests/test_profile_publication_service_update.py tests/test_cv_projects_update.py -q`

Expected: all focused tests pass.

### Task 4: Build and Visual Verification

**Files:**
- Verify all modified files and generated `_site` output

**Interfaces:**
- Consumes: Tasks 1-3
- Produces: verified bilingual responsive homepage

- [ ] **Step 1: Run formatting and full tests**

Run: `git diff --check && python3 -m pytest -q`

Expected: no whitespace errors; full suite passes with only pre-existing skips.

- [ ] **Step 2: Build Jekyll**

Run: `BUNDLE_PATH=/private/tmp/shuolv-jekyll-bundle bundle exec jekyll build`

Expected: successful build with no Liquid/Markdown errors.

- [ ] **Step 3: Inspect generated HTML semantics**

Confirm contribution summaries and Key outcomes are absent, internship/project headings are visible, local logos resolve, Human Intelligence has only placeholder details, and the toolkit exposes two categories.

- [ ] **Step 4: Visually inspect desktop and mobile English/Chinese pages**

Check the 2:8 publication cards, logo proportions, internship row alignment, first-level heading hierarchy, mobile stacking, and absence of overlaps or broken images.

- [ ] **Step 5: Review final diff and report without committing implementation**

Run: `git status --short && git diff --stat && git diff --check`

Expected: only intended source, test, and logo changes plus the user's pre-existing working-tree changes.
