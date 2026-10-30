# Homepage Interns and Projects Refinement Design

## Scope

Refine the bilingual homepage publication, research-interest, internship/project, and technical-toolkit sections. English remains the default site language. Every visible content and layout change is mirrored in Chinese, except that company names retain their official branding.

## Publication Cards

- Keep the existing publication metadata, links, figures, typography, order, and mobile behavior.
- Change the desktop image-to-text grid from `3:7` to `2:8`.
- Hide each contribution summary by wrapping the existing `.pub-highlight` markup in source comments. Do not delete the descriptions.
- Keep the current single-column mobile layout and proportional image scaling.

## Research Interests

- Keep the three existing research-interest headings and their introductory paragraphs.
- Hide every `Key outcomes` / `代表性成果` label and list in source comments rather than deleting them.
- Replace the AI4Science paragraph with a concise, forward-looking statement about using LLM agents to accelerate scientific discovery, automate research workflows, and support verifiable reasoning.
- Do not mention ByteDance or describe employment history in the AI4Science paragraph.

## Interns and Projects

- Replace the collapsed `Recent Projects` / `近期项目` block with a visible top-level section titled `Interns and Projects` / `实习与项目`.
- The section is the same heading level as Publications and is expanded by default because it no longer uses a `<details>` container.
- Add a second-level `Intern Experience` / `实习经历` subsection before projects.
- Render internship entries with the same visual structure as Education: a locally stored logo at left and company, location/date, role, and concise work description at right.
- First internship: ByteDance Seed Foundation Model, AI4Math; use the existing CV and project copy as the source of truth for Nov. 2025-May 2026, role, and work. Use a verified public company location only if one is available in repository evidence or official public material.
- Second internship: Human Intelligence / 智能知识. Until the user supplies details, show the company name and `Details forthcoming` / `详情待补充`; do not invent time, location, role, or responsibilities.
- Obtain company logos from official or publicly maintained brand material, store them locally, preserve aspect ratio, and provide meaningful alt text.
- Add a second-level `Projects` / `项目经历` subsection after internships.
- Preserve the six non-ByteDance project entries and their current order and wording. Move ByteDance out of the project list so it appears only under Intern Experience.

## Technical Toolkit

- Keep `Programming` / `编程语言` and `Neuroimaging & research` / `神经影像与科研` visible.
- Hide `Machine learning` / `机器学习` and `Agents & language models` / `智能体与大语言模型` in source comments rather than deleting them.
- Do not otherwise change the Skills section.

## Responsive and Accessibility Requirements

- Internship rows match the Education layout on desktop and remain readable without overlap on mobile.
- Logos use local files, explicit alt text, lazy loading, and proportional sizing.
- Existing heading anchors remain stable (`#projects`, `#publications`, and `#research`) so navigation and internal links continue to work.

## Verification

- Add or update focused tests for bilingual heading parity, visible/hidden content, publication ratio, expanded project content, internship ordering, and toolkit visibility.
- Run the complete test suite and a Jekyll production build.
- Visually inspect English and Chinese pages at desktop and mobile widths, including image loading and the new internship layout.
