# Guoyuan Yang Academic CV Design

## Goal

Create a standalone English academic CV for Guoyuan Yang by reusing the visual language and LaTeX structure of `assets/files/cv_en.tex`. The existing CV must remain unchanged.

## Output

- Source: `assets/files/cv_guoyuan_yang_en.tex`
- Compiled document: `assets/files/cv_guoyuan_yang_en.pdf`
- Compiler: XeLaTeX

## Content and Structure

The CV will use the existing template's typography, colors, section rules, contact row, and compact entry formatting, while allowing the document to span multiple pages. It will contain:

1. Header with `Guoyuan Yang`, `Associate Professor`, disciplines, email, office, homepage, ORCID, GitHub organization, and a clearly marked phone placeholder in the source.
2. Academic Appointments.
3. Education.
4. Research Interests.
5. Publications containing all 18 publications listed on the BIT faculty page, preserving author order and contribution notes.
6. Research Grants and Projects.
7. Patents.
8. Book.

Teaching courses are intentionally excluded.

## Sources and Identity Checks

- The BIT faculty page is the primary source for appointments, education, research interests, publications, grants, patents, book, email, and office.
- ORCID `0000-0002-7864-3714` is accepted because its verified `bit.edu.cn` domain, employment, research field, and publications match the faculty profile.
- GitHub will link to the verified lab organization `BIT-YangLab`; its repository names Guoyuan Yang and `yanggy@bit.edu.cn` as the contact.
- No Google Scholar link will be included unless a profile can be tied unambiguously to the same person. Current search results do not provide that confirmation.

## Translation and Formatting Rules

- Use `Associate Professor` exactly as requested.
- Translate Chinese institutional and project names into concise formal English without inventing credentials.
- Preserve publication titles in their published English form.
- Escape LaTeX special characters and allow URLs to break safely.
- Keep a compact academic-CV style, but prioritize legibility over forcing content into a fixed page count.

## Verification

Compile with XeLaTeX at least twice, confirm a successful exit, inspect the log for overfull boxes and missing glyphs, and render/check every PDF page for clipping or broken layout. Do not modify `assets/files/cv_en.tex`.
