# CV Sidebar and Recent Projects Update Design

## Goal

Update the bilingual academic homepage so both September 2026 CVs are downloadable from the profile sidebar and the English and Chinese Recent Projects sections accurately reflect the supplied CVs.

## Sources of Truth

- English CV: `/Users/shuolv/Desktop/Code/Secmind/output/pdf/Shuo_Lv_Academic_CV_Template.pdf`
- Chinese CV: `/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.pdf`

The supplied CVs control project names, dates, roles, methods, metrics, publication outcomes, and awards. The homepage may expand the prose for readability, but it must not introduce unsupported claims.

## Scope

### CV downloads

- Copy the English PDF to `assets/files/CV202609_EN.pdf` and the Chinese PDF to `assets/files/CV202609_ZH.pdf`.
- Replace the single `author.cv` configuration value with separate English and Chinese CV values.
- Show two labeled PDF links on both language versions of the desktop sidebar.
- Show two distinct PDF links in the compact mobile profile controls, each with an accessible language label.
- Use localized labels:
  - English page: `CV (English, Sep 2026)` and `CV (Chinese, Sep 2026)`.
  - Chinese page: `英文简历（2026 年 9 月）` and `中文简历（2026 年 9 月）`.

### Recent Projects

Keep the existing native `<details markdown="1">` disclosure and established visual styling. Replace the current eight-project list with seven CV-backed entries in this order:

1. General-Purpose Cybersecurity Agent
2. ByteDance Seed AI4Math Research Internship
3. Low-Dimensional Spatiotemporal Dynamics of the Human Brain
4. Complex Social Awareness Modeling
5. Intelligent Factory Security
6. Large Language Model for Early Childhood Education
7. Xiangqi Game-Playing System

The ByteDance entry remains one umbrella item with three clearly labeled workstreams:

- MathNL TTS multi-agent reasoning: five iterations, more than 100 problems, and a 6.4/7 average on the stated IMO problem set.
- Automated Lean 4 proof QA: more than 600 formalized data items and more than 70% improvement in expert review efficiency.
- Evaluation-data operations: more than 2,000 delivered data items and 11 production and quality specifications.

The cybersecurity entry adds the CV-backed architecture and safety details: five specialized agents, a 16-node bounded state machine, R0-R3 risk levels, Finding-Evidence validation, human approval for high-risk actions, and the two-layer state/domain blackboard.

Remove the Smart Cultural Tourism System and Leadership Evaluation Framework Under Polygenic Risk because neither appears in the supplied September 2026 CVs. Remove earlier unsupported MathNL claims about seven fixed roles and thousands of runtime actions.

Keep the remaining five project entries aligned with the current CV wording, including exact dates, roles, methods, publication outcomes, and awards. Preserve concise website prose while allowing more detail than the PDFs.

### Bilingual synchronization

- Maintain equivalent facts, ordering, metrics, and dates in the English and Chinese project includes.
- Use natural language in each version instead of literal word-for-word translation.
- Update both homepage footers to September 2026.

## Implementation Boundaries

- Modify only the CV configuration, profile sidebar template, bilingual Recent Projects includes, bilingual homepage update timestamps, and relevant tests/assets.
- Preserve the existing homepage layout, disclosure behavior, typography, colors, and other profile links.
- Do not alter either source PDF.
- Do not touch unrelated pending changes in `protected_phd_agent/`.
- Do not redesign or deploy through a different hosting system; this repository remains a GitHub Pages Jekyll site.

## Validation

- Add source-level regression tests for both configured CV paths, both desktop sidebar labels/links, accessible mobile links, the seven-project count, bilingual project order, required CV-backed metrics, removal of unsupported claims, and September 2026 timestamps.
- Confirm both copied PDF assets exist and match the supplied source files byte-for-byte.
- Run the complete existing test suite.
- Build the Jekyll site successfully.
- Inspect the generated English and Chinese homepage HTML to confirm both CV links resolve and the project disclosure renders seven entries without raw Markdown.

## Non-goals

- No broader biography, education, publication, award, skill, or navigation rewrite.
- No visual redesign of the sidebar or project disclosure.
- No changes to the supplied PDF contents.
- No restoration of projects omitted from the current CVs.
