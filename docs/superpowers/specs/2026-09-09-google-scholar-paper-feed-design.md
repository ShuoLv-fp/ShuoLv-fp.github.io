# Google Scholar Paper Feed Design

**Date:** 2026-09-09
**Status:** Approved for implementation planning

## 1. Purpose

Add a public, automatically updated paper-reading page to the existing bilingual Jekyll site. A daily GitHub Actions workflow will read Google Scholar alert emails from `lv_shuo@foxmail.com`, enrich each paper with a publicly available abstract when possible, generate concise Chinese and English summaries with DeepSeek, and publish the results as a seven-day paginated feed.

The feature is intended to make daily literature discovery convenient without turning the existing homepage into a long news stream.

## 2. Goals

- Read only Google Scholar alert messages through Foxmail IMAP.
- Collect every paper found in matching alerts.
- Merge duplicate papers without publicly revealing which subscribed author triggered an alert.
- Prefer public abstracts over email snippets as the summary source.
- Generate bilingual summaries, topic tags, research-relevance explanations, and relevance levels.
- Publish a dedicated English and Chinese paper-feed page linked from the main navigation.
- Show a continuous seven-calendar-day window and allow navigation backward and forward by seven days.
- Fail safely: preserve the last good public feed when email authentication or a pipeline-wide operation fails.
- Keep email credentials, API credentials, raw email content, and mailbox identifiers out of the repository and public site.

## 3. Non-goals

- Downloading or redistributing paywalled full-text papers.
- Claiming that a full paper was read when only an abstract or email snippet was available.
- Displaying subscribed-author provenance, alert sender details, raw messages, or mailbox metadata.
- Providing user accounts, access control, comments, recommendations, or collaborative reading features.
- Making the first version a full-text semantic search or reference-management system.
- Using the vision capability of the selected model in the first version.

## 4. User Experience

### 4.1 Navigation and routes

Add a separate top-level navigation item:

- English: `Paper Feed` → `/paper-feed/`
- Chinese: `学术速递` → `/zh/paper-feed/`

The existing homepage content remains unchanged except for the new navigation link. Switching between English and Chinese on a paper-feed page must preserve the selected date window.

### 4.2 Seven-day pagination

- The initial view covers the latest seven calendar days in the `Asia/Shanghai` timezone, including the current date.
- Dates with no papers are omitted as visual sections, but the page window still represents exactly seven consecutive calendar days.
- `Previous 7 days / 前 7 天` moves the window backward by seven days.
- `Next 7 days / 后 7 天` moves the window forward by seven days and is hidden or disabled on the latest window.
- `Latest / 最新` returns to the current seven-day window.
- The start date is stored in the query string, for example `?start=2026-09-03`, so a historical window can be bookmarked or shared.
- Invalid, future, or malformed start dates fall back to the latest valid window.

### 4.3 Confirmed visual direction

Use the approved **magazine-style large-card layout (Option B)**:

- A compact page introduction and date-range toolbar appear at the top.
- Papers are grouped under prominent date markers and ordered newest date first.
- Cards show the full generated summary without requiring an expand action.
- The layout is a single readable column on mobile and may use a narrow date rail beside the content on wider screens.
- Styling follows the site's existing academic visual language, typography, dark mode, and responsive behavior.
- Pagination controls appear at both the top and bottom when the feed is long.

### 4.4 Paper card fields

Each public card contains only:

- Relevance badge: `Highly relevant / 高度相关`, `Transferable / 可借鉴`, or `Weakly related / 弱相关`.
- Original paper title.
- Public author list when available.
- Venue or preprint platform and publication year when available.
- One-sentence core conclusion in the current page language.
- Two or three concise research points in the current page language.
- A short explanation of the connection to Shuo Lv's research.
- Topic tags.
- Original paper or landing-page link.
- Evidence label: `Public abstract / 公开摘要` or `Email snippet / 邮件片段`.

The card and public data must not contain the subscribed author that triggered the alert, the alert sender, recipient addresses, message identifiers, mailbox folder names, or raw email HTML.

### 4.5 Ordering

Within each date, cards are ordered by:

1. Relevance level: highly relevant, transferable, weakly related.
2. Ingestion time, newest first.
3. Normalized title as a stable final tie-breaker.

All collected papers are retained regardless of relevance level.

## 5. System Architecture

The feature consists of five isolated units.

### 5.1 Scheduled workflow

A dedicated GitHub Actions workflow runs once daily and also supports manual dispatch. It:

1. Checks out the repository.
2. Installs the pinned Python dependencies.
3. Runs the paper-feed processor.
4. Validates the generated public data.
5. Commits and pushes only when the validated data changed.

A successful data commit triggers the existing GitHub Pages deployment workflow. The scheduled workflow receives only the minimum required repository permission (`contents: write`). Pull-request workflows must never receive the email or DeepSeek secrets.

### 5.2 Mail reader and parser

The mail unit connects using IMAP over TLS and uses a non-mutating fetch mode so messages remain unread if they were unread before processing.

Selection uses a configurable combination of:

- Known Google Scholar alert sender addresses.
- Recognized alert subject patterns.
- Required structural markers in the HTML or plain-text body.

Sender or subject matching alone is insufficient. Messages that do not pass all configured checks are ignored.

The parser emits a minimal internal paper candidate containing title, public authors if present, paper link, email snippet, and alert arrival time. It does not pass unrelated email content downstream.

### 5.3 Metadata enrichment

For each candidate, the enrichment unit attempts to resolve a stable paper identifier and public abstract using this order:

1. DOI metadata and publisher meta tags.
2. arXiv identifier and API metadata.
3. PubMed or Europe PMC metadata.
4. OpenAlex metadata.
5. A safe, bounded fetch of the linked public landing page.
6. Google Scholar email snippet as the final fallback.

Network requests use timeouts, response-size limits, redirects limits, a descriptive user agent, and retry rules. HTML is parsed as untrusted input; scripts, styles, hidden content, and instructions embedded in pages are discarded.

### 5.4 Summary and relevance service

The summarizer uses DeepSeek's OpenAI-compatible API:

- Base URL: `https://api.deepseek.com`
- Model: `deepseek-v4-flash-vision-exp`
- Credential source: GitHub Secret `DEEPSEEK_API_KEY`
- Model configuration source: a normal workflow variable or repository configuration, not hard-coded business logic

The selected model is experimental, so the model name remains configurable. Replacing it must not require changes to parsing, storage, or page rendering.

The request contains only the normalized paper metadata, public abstract or selected email snippet, and a concise public research-interest profile. It never contains raw messages or mailbox identifiers. The model receives explicit instructions to treat paper text as quoted research material rather than executable instructions.

The response uses a strict JSON schema containing bilingual conclusions, bilingual bullet points, bilingual relevance explanations, bilingual tags, and a relevance enum. Schema validation, bounded retry, and length validation occur before any result is published.

### 5.5 Public data and rendering

The processor writes one canonical bilingual JSON data file under the site's published assets. Both language pages load the same records and select the appropriate localized fields in the browser.

The public record contains:

- Stable public record ID derived from DOI, arXiv ID, canonical URL, or normalized title hash.
- Title, public authors, venue, year, and canonical source URL.
- Alert date and ingestion timestamp.
- Summary evidence type.
- English and Chinese generated fields.
- Relevance enum and localized tags.
- Processing status only when a permanent metadata-only fallback is published.

No private processing state is stored in the public record. Duplicate detection uses public scholarly identifiers and normalized title hashes, not email message IDs.

The browser-side renderer performs date-window selection, grouping, ordering, URL-state handling, and language selection. It inserts user-visible text through safe text operations rather than raw HTML.

## 6. Processing Flow

1. Determine the last successful ingestion point from the existing public data and a conservative overlap window.
2. Retrieve only matching Scholar alerts with a bounded look-back.
3. Parse minimal paper candidates.
4. Normalize URLs and titles.
5. Deduplicate by DOI, then arXiv ID, then canonical URL, then normalized title hash.
6. Enrich metadata and choose the strongest available evidence source.
7. Request one structured bilingual DeepSeek result per new paper.
8. Validate content, lengths, URLs, enum values, and absence of forbidden private fields.
9. Merge valid records with existing public records without changing stable historical summaries unnecessarily.
10. Write data atomically, run repository tests and a production Jekyll build, then commit if content changed.

The first manual run uses a bounded 30-day look-back. Subsequent runs use a seven-day overlap window to catch delayed alerts and retry incomplete papers at least three times. This avoids scanning the whole mailbox while seeding more than one page of history.

## 7. Failure and Recovery Rules

### 7.1 Per-paper failure

- Temporary metadata or DeepSeek failures increment a retry counter in non-site processing state and leave the item unpublished.
- The next scheduled run retries the item.
- After three failed runs, publish a metadata-only card with the source link and localized `Summary temporarily unavailable / 摘要暂不可用` message.
- A later successful run replaces the fallback with a normal summarized record.

Persist retry state in a Jekyll-excluded repository file so it survives across GitHub Actions runs. Each entry contains only a stable public paper ID, retry count, last-attempt date, and sanitized error category. It must never contain raw messages, email addresses, subscription-source authors, or message identifiers.

### 7.2 Pipeline-wide failure

Email authentication failure, public-data validation failure, an unexpected parser-wide error, or a failed site build aborts the update. The last good feed remains published and no partial file is committed.

### 7.3 Duplicate alerts

The same paper may arrive through several followed authors or repeat alerts. All candidates merge into one public record. Triggering-author provenance is discarded before storage and never rendered.

### 7.4 Observability

Workflow logs may contain counts, public record IDs, paper titles, and error categories. They must not print secrets, raw email bodies, mailbox identifiers, or full model requests. A concise GitHub Actions job summary reports:

- Matching alerts processed.
- New, duplicate, summarized, deferred, and metadata-only paper counts.
- Whether public data changed.
- Sanitized failure categories and recommended operator action.

## 8. Configuration and Secrets

Required GitHub Secrets:

- `FOXMAIL_USERNAME`
- `FOXMAIL_IMAP_AUTH_CODE`
- `DEEPSEEK_API_KEY`

Normal configuration:

- IMAP host, TLS port, and mailbox folder.
- Scholar sender allowlist and subject patterns.
- Daily schedule and timezone assumptions.
- DeepSeek base URL and model name.
- Metadata request timeouts and retry limits.
- Initial and recurring look-back windows.
- Public research-interest profile used for relevance classification.

The Foxmail credential must be a third-party IMAP authorization code, not the account's primary password. Credentials are entered directly in GitHub repository settings and are never supplied in chat, committed, echoed, or copied into generated files. Any credential disclosed in chat must be revoked before implementation testing.

## 9. Proposed Project Boundaries

Keep responsibilities separate so they can be tested and replaced independently:

- `paper_feed/mail.py`: secure IMAP selection and minimal message retrieval.
- `paper_feed/parser.py`: Scholar alert parsing and candidate normalization.
- `paper_feed/metadata.py`: scholarly identifiers and public abstract enrichment.
- `paper_feed/summarizer.py`: DeepSeek request, schema, validation, and retry handling.
- `paper_feed/store.py`: deduplication, merge, ordering, and atomic JSON writes.
- `paper_feed/main.py`: orchestration and command-line dry-run/publish modes.
- `assets/js/paper-feed.js`: date-window navigation and safe rendering.
- Focused Jekyll includes/pages and Sass for the approved magazine layout.

Exact filenames may be adjusted during implementation planning to match repository conventions, but these module boundaries must remain.

## 10. Testing Strategy

### 10.1 Unit tests

- HTML and plain-text alert parsing using sanitized fixtures.
- Malformed message, unexpected encoding, and missing-field handling.
- DOI, arXiv ID, URL, and normalized-title deduplication.
- Metadata-source priority and fallback behavior.
- DeepSeek JSON schema validation, bounded retries, and bilingual length constraints.
- Relevance ordering and stable tie-breaking.
- Seven-day range calculations around month and year boundaries.
- Query-string validation and latest-window behavior.
- HTML escaping and forbidden-field checks.

### 10.2 Integration tests

- Dry-run from sanitized alert fixture to validated public JSON.
- Mocked IMAP and metadata/API failures.
- Three-run failure transition to metadata-only fallback.
- Reprocessing the same alerts produces no duplicate records and no unnecessary commit.
- English and Chinese pages render the same record set and date window.
- Switching language preserves the selected start date.

### 10.3 Site verification

- Production Jekyll build succeeds.
- Existing homepage presentation tests remain green.
- Desktop and mobile visual checks cover light and dark mode.
- Navigation, both language routes, pagination controls, original links, and empty windows work.
- A focused scan confirms paper-feed data, processing state, and workflow logs contain no secret values, mailbox addresses, raw email bodies, subscription-source authors, or message identifiers. The site's existing public contact address is outside this check.

## 11. First-run Procedure

1. Revoke the DeepSeek API key that was disclosed in chat and create a new key.
2. Enable Foxmail IMAP and create a dedicated third-party authorization code.
3. Add all three required values directly to GitHub Actions Secrets.
4. Run a local or CI dry-run against sanitized fixtures.
5. Run a manual live 30-day ingestion in preview mode without committing.
6. Review record counts, representative Chinese and English cards, relevance ratings, and the sanitized Actions summary.
7. Enable publishing and verify the deployed routes.
8. Leave the daily schedule active after the first successful deployment.

## 12. Acceptance Criteria

- The English and Chinese navigation bars open separate paper-feed pages.
- Both pages show the same papers in the approved magazine-style large-card layout.
- The latest view covers exactly seven Shanghai calendar days, with working seven-day pagination and bookmarkable URLs.
- New Scholar alerts are ingested daily without changing message read state.
- Duplicate alerts yield one card and never expose the triggering subscribed author.
- Every successful card has a valid original link, an evidence label, complete bilingual generated fields, tags, relevance, and a research-connection explanation.
- Papers at all relevance levels are retained and correctly ordered.
- Three consecutive per-paper failures lead to a clear metadata-only fallback rather than permanent loss.
- Pipeline-wide failure never replaces the last valid public data.
- No credentials, raw messages, mailbox identifiers, subscribed-author provenance, or alert recipient/sender metadata appear in paper-feed files, the generated feed pages, or workflow logs. This does not remove the site's existing public contact address.
- All automated tests and the production Jekyll build pass before publication.

## 13. Approved Decisions Summary

- Hosting and automation: existing GitHub Pages repository plus GitHub Actions.
- Visibility: public.
- Collection: all papers, ordered and labeled by research relevance.
- Languages: Chinese and English.
- Location: dedicated pages reached through the top navigation, not a homepage section.
- Pagination: continuous seven-calendar-day windows.
- Layout: Option B, magazine-style large cards with summaries visible by default.
- Model: DeepSeek `deepseek-v4-flash-vision-exp`, configurable because it is experimental.
- Privacy: subscription-trigger authors and all mailbox metadata are private and must be discarded before public storage.
