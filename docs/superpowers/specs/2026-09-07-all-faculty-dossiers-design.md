# All Faculty Dossiers Design

## Problem

Production stores 238 faculty records, including 28 records with a positive
`featured_rank`. The browser currently builds its dossier list by filtering out every
record without a positive `featured_rank`, so the 210 newly added records are loaded
but never rendered.

## Approved behavior

- Show all faculty records in the existing Advisor dossiers list.
- Keep featured records first, ordered by ascending `featured_rank`.
- Order all remaining records by descending `fit.total`, with display name and
  institution as stable alphabetical tie-breakers.
- Keep search, dossier detail, status editing, drafts, and cloud synchronization
  behavior unchanged.
- Rename curated-only count labels so they describe the complete advisor collection.
- Do not mutate production data or assign featured ranks to the new records.

## Implementation boundary

Introduce one small pure ordering function that can be tested without the DOM. The
existing UI will use that function wherever it obtains dossier rows. The supporting
browser asset remains protected by the same authenticated asset gate as `app.js`.

## Verification

- A failing unit test must first demonstrate that unfeatured records are omitted by
  the current behavior.
- Unit tests will cover featured-first ordering, fit-score ordering, and deterministic
  tie-breaking.
- Worker tests will confirm that the helper asset is unavailable before login and
  served after login.
- The complete JavaScript and Python test suites and a production dry run must pass.
- After deployment, an authenticated bootstrap/list check must show 238 records while
  preserving the 28 featured records.
