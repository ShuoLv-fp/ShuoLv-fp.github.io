# Homepage Publication and Section Formatting Design

## Goal

Repair the homepage presentation without changing its overall visual style or rewriting the existing content.

## Scope

- Replace the placeholder image for “Impact of Sampling Disease Detection and Collective Intervention Measures in Epidemic Transmission” with a crop from Fig. 2 of the supplied Springer chapter.
- Fix Markdown rendering inside the Recent Projects and Teaching Experience disclosure panels.
- Hide Passions & Hobbies and Collaborators and friends while preserving their source for later restoration.
- Keep the English and Chinese homepages synchronized.

## Design

### Publication image

Use the central Fig. 2 diagram from PDF page 4 because it directly depicts sampling disease detection connecting the physical epidemic network with the statistical-state layer. Crop out the surrounding paper text, page header, and figure caption. Export a lossless PNG plus an optimized WebP and update both language versions of the publication card to use the new descriptive asset paths.

### Collapsible sections

Retain the native `<details>` and `<summary>` interaction. Add Kramdown's `markdown="1"` attribute to the `<details>` containers in Recent Projects and Teaching Experience so headings, emphasis, and lists are converted to HTML instead of appearing as raw Markdown. Apply the same change to English and Chinese includes.

### Temporarily hidden sections

Wrap the Passions include and the Collaborators section in Liquid `{% comment %}` blocks in both homepage files. Do not delete or rewrite the underlying content.

## Verification

- A source-level regression check must fail before the fix and pass afterward, covering both languages, both Markdown disclosure panels, the publication image references, and the hidden sections.
- The Jekyll build must complete successfully.
- Render and inspect both `/` and `/zh/` at desktop width, confirming that no raw `**`, Markdown list markers, or heading markers remain in the expanded panels.
- Confirm the new publication crop is legible, aligned with the existing publication cards, and opens correctly through the existing lightbox.

## Non-goals

- No redesign of publication cards or disclosure panels.
- No edits to project or teaching wording.
- No deletion of hobby or collaborator content.
