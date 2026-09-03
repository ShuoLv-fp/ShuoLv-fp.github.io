# Autism Paper Acceptance Update — Design Specification

## Objective

Synchronize the newly accepted autism paper across the English CV, Chinese CV, and the bilingual personal homepage. The publication must appear third, immediately after Shuo Lv's two independent first-author papers.

## Authoritative publication metadata

- Final title: **Alterations in functional brain network topography in autism revealed by normative models**
- Journal: *Translational Psychiatry*
- Status: accepted in September 2026; not yet published online
- Public full-text link while awaiting publication: <https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1>
- DOI, volume, issue, article number, and pages: omit until the final article is online
- Author order: preserve the current order exactly
- Homepage publication image: preserve `/images/pub/pub_biorxiv_autism.webp`
- Homepage code link: preserve the existing repository link

## English CV

- Update the title to the final accepted title.
- Move the entry to position three in `Selected Publications`, after the two independent first-author papers.
- Keep the title linked to the bioRxiv preprint.
- Replace the bioRxiv-only venue line with an accepted-publication line naming *Translational Psychiatry* and September 2026, without invented bibliographic fields.
- Update the related research-experience summary so it no longer says the manuscript is under review.
- Preserve the one-page A4 layout.

## Chinese CV

- Edit the existing matching Word source file and regenerate the repository PDF.
- Update the title, journal, acceptance date, and ordering in the publications section using the same metadata policy as the English CV.
- Keep the author order unchanged.
- Preserve the current two-page A4 visual design and all unrelated content.

## Bilingual homepage

- Update the English and Chinese publication cards with the final title and September 2026 acceptance by *Translational Psychiatry*.
- Keep the bioRxiv title link, author order, publication image, and code link unchanged.
- Keep the card in third position after the two independent first-author journal papers.
- Rewrite the short highlight to describe altered functional brain-network topography in autism rather than language-network expansion.
- Update related English and Chinese research-interest or recent-project summaries so they no longer say the manuscript is under review.
- Do not edit either language's News section.

## Verification

- Add or update automated checks for title, journal, acceptance date, ordering, preserved author order, preserved image, preserved preprint link, and absence of the old title/under-review wording outside News.
- Compile the English CV and confirm it remains one A4 page with working links.
- Render the Chinese Word source and regenerated PDF, visually inspect both pages, and confirm layout fidelity.
- Build the site and inspect the affected bilingual publication sections.
- Confirm News files are unchanged.

## Deliverables

- Updated bilingual homepage sources
- Updated `assets/files/cv_en.tex`
- Updated `assets/files/CV202609_EN.pdf`
- Updated `assets/files/CV202609_ZH.pdf`
- Updated matching Chinese CV Word source outside the repository, retained as the editable source
