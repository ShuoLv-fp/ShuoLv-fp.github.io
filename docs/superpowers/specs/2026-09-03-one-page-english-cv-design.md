# One-Page English CV Design

## Objective

Revise `assets/files/cv_en.tex` and regenerate `assets/files/CV202609_EN.pdf` as a polished, link-enabled, one-page academic CV. The CV should follow the facts already published on the personal homepage and the dates confirmed by the author.

## Page and Typography

- Keep an A4, single-column academic layout.
- Start with horizontal margins of approximately 0.45 in and vertical margins of approximately 0.35 in, then tune spacing only as needed to obtain exactly one page without clipping or illegible text.
- Preserve the existing compact serif visual style and clear section hierarchy.
- Remove the forced page break. Reduce vertical whitespace, list indentation, and repeated wording before considering a meaningful reduction in type size.

## Header

- Keep the author's name and the existing research-keyword line.
- Remove date of birth and telephone number.
- Add a compact, clickable icon row for email, location, homepage, GitHub, Google Scholar, and ORCID.
- Use the homepage URLs as the source of truth:
  - Email: `lv_shuo@foxmail.com`
  - Location: Beijing, China
  - Homepage: `https://ShuoLv-fp.github.io`
  - GitHub: `https://github.com/ShuoLv-fp`
  - Google Scholar: `https://scholar.google.com/citations?user=VAsm0T8AAAAJ`
  - ORCID: `https://orcid.org/0009-0009-2540-0485`

## Education

- Follow the reference image's two-line structure: institution and location on the first line; abbreviated degree and dates on the second line.
- Beijing Institute of Technology — Beijing, China — Sep. 2024–Present:
  - `M.Eng. in Electronic Information (Biomedical Engineering)`
- Southwest University — Chongqing, China — Sep. 2020–Jun. 2024:
  - `B.Eng. in Data Science and Big Data Technology`
- Remove discipline codes.
- Do not repeat the BIT research interests, because they already appear beneath the name.
- Keep the SWU ranking and scholarships in one compact supporting line.
- Leave optional GPA and coursework fields commented in the source rather than showing empty labels in the PDF.

## Publications

- Keep all six selected publications.
- Preserve author order, venue, volume, pages/article number, and year.
- Make each paper title the clickable link and remove visible DOI/URL strings to save space.
- Use a compact numbered or hanging-indented list with minimal vertical spacing.

## Experience

- Keep `Research Internship` and `Research Experience` as separate sections.
- Keep the ByteDance internship and all six research projects.
- Compress each entry into one concise paragraph while retaining the strongest quantitative results and technical substance.
- Replace `Project Lead` with conventional role labels:
  - `Lead Researcher` for research projects where the author was responsible for the work;
  - `Lead Developer` for the Xiangqi system;
  - `Researcher` for the early-childhood education project.
- Retain advisor attribution in a compact inline form.
- Avoid repeating award details inside experience paragraphs when the same result appears in `Awards and Honors`.

## Awards and Skills

- Keep all five awards, using a space-efficient three-column layout.
- Keep the existing technical-skills categories and content, tightening row spacing where necessary.

## Output and Validation

- Add the revised `assets/files/cv_en.tex` to version control.
- Regenerate the file already referenced by the homepage: `assets/files/CV202609_EN.pdf`.
- Verify that the PDF has exactly one A4 page, contains no clipped or overlapping text, and has working links for the header profiles and every publication title.
- Render the final PDF to an image and visually inspect it before committing and pushing to the current remote branch.
