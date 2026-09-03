# Curated Index Status and Independent Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the curated advisor index fixed with its own scroll area on desktop and show each advisor's current `YOUR NOTES` contact status in the index.

**Architecture:** Preserve the existing single-page, dependency-free rendering model. CSS makes the left index a sticky, viewport-height grid whose list is the only vertically scrolling child; JavaScript derives a normalized display status from `row.status` and updates the matching badge in place when the notes selector changes.

**Tech Stack:** Vanilla JavaScript, CSS, HTML, Vitest, Cloudflare Workers static assets

## Global Constraints

- Only the `CURATED INDEX` and its rendering behavior may change.
- Use the existing `row.status` field and `markDirty` synchronization path; do not add or migrate data fields.
- Desktop uses independent vertical scrolling; widths at or below 780px retain the existing horizontal advisor list.
- Supported display states are `Discovered`, `Shortlisted`, and `Contacted`; invalid or missing values fall back to `Discovered`.
- Preserve all existing advisor, email, application, and profile data.

---

### Task 1: Make the desktop curated index independently scrollable

**Files:**
- Modify: `protected_phd_agent/test/static.test.js`
- Modify: `protected_phd_agent/public/style.css`

**Interfaces:**
- Consumes: existing `.dossier-shell`, `.advisor-index`, `.advisor-index-head`, and `.dossier-nav` elements.
- Produces: a sticky `.advisor-index` with a viewport-height grid and a scrollable `.dossier-nav`; mobile resets these constraints.

- [ ] **Step 1: Write the failing test**

Add a static UI test that asserts the stylesheet contains the desktop sticky index contract and the mobile reset:

```js
it("keeps the curated advisor index independently scrollable on desktop", async () => {
  const { css } = await uiSources();
  expect(css).toContain(".advisor-index { background: #f6f9f9;");
  expect(css).toContain("position: sticky");
  expect(css).toContain("grid-template-rows: auto minmax(0, 1fr)");
  expect(css).toContain(".dossier-nav { min-height: 0; overflow-y: auto;");
  expect(css).toContain(".advisor-index { border-bottom: 1px solid var(--line); border-right: 0; display: block; height: auto; overflow: visible; position: static; }");
});
```

Extend `uiSources()` to fetch `/style.css` and return it as `css`.

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
pnpm test -- test/static.test.js -t "keeps the curated advisor index independently scrollable on desktop"
```

Expected: FAIL because `.advisor-index` is not sticky or viewport-height and the mobile reset is absent.

- [ ] **Step 3: Implement the minimum CSS behavior**

Update the desktop rules so `.advisor-index` uses `align-self: start`, `display: grid`, `grid-template-rows: auto minmax(0, 1fr)`, `height: calc(100vh - 96px)`, `overflow: hidden`, `position: sticky`, and `top: 96px`. Remove sticky positioning from `.advisor-index-head`. Change `.dossier-nav` to `min-height: 0; overflow-y: auto` without its existing `max-height` calculation.

In the 1040px media query, set `.advisor-index` to `height: calc(100vh - 137px); top: 137px`. In the 780px media query, reset `.advisor-index` to `display: block; height: auto; overflow: visible; position: static`, and retain the horizontal `.dossier-nav` behavior.

- [ ] **Step 4: Run the focused test to verify it passes**

Run the focused command from Step 2.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add protected_phd_agent/test/static.test.js protected_phd_agent/public/style.css
git commit -m "fix: decouple advisor index scrolling"
```

### Task 2: Show and immediately update contact status in each advisor entry

**Files:**
- Modify: `protected_phd_agent/test/static.test.js`
- Modify: `protected_phd_agent/public/app.js`
- Modify: `protected_phd_agent/public/style.css`

**Interfaces:**
- Consumes: `row.status`, the existing `#advisor-status` selector, and `markDirty(collection, id, patch)`.
- Produces: `advisorStatus(value)` returning `{ key, label }`, badge ids in the form `advisor-contact-status-${row.id}`, and `updateAdvisorStatusBadge(row)` for in-place synchronization.

- [ ] **Step 1: Write the failing test**

Add a static UI test that verifies the status model, badge rendering, and immediate update path:

```js
it("shows and immediately updates each advisor contact status in the curated index", async () => {
  const { appJs, css } = await uiSources();
  expect(appJs).toContain("function advisorStatus(value)");
  expect(appJs).toContain('label: "Discovered"');
  expect(appJs).toContain('label: "Shortlisted"');
  expect(appJs).toContain('label: "Contacted"');
  expect(appJs).toContain('id: `advisor-contact-status-${row.id}`');
  expect(appJs).toContain("updateAdvisorStatusBadge(row)");
  expect(css).toContain(".contact-status");
  expect(css).toContain(".contact-status.contacted");
});
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
pnpm test -- test/static.test.js -t "shows and immediately updates each advisor contact status in the curated index"
```

Expected: FAIL because the status helper, badge, and styles do not exist.

- [ ] **Step 3: Implement normalized status rendering and in-place synchronization**

Add:

```js
function advisorStatus(value) {
  const statuses = {
    discovered: { key: "discovered", label: "Discovered" },
    shortlisted: { key: "shortlisted", label: "Shortlisted" },
    contacted: { key: "contacted", label: "Contacted" }
  };
  return statuses[value] || statuses.discovered;
}

function updateAdvisorStatusBadge(row) {
  const badge = document.getElementById(`advisor-contact-status-${row.id}`);
  if (!badge) return;
  const status = advisorStatus(row.status);
  badge.className = `contact-status ${status.key}`;
  badge.textContent = status.label;
}
```

In each advisor tab, replace the lone fit chip with an `.advisor-tab-signals` wrapper containing the existing score and a `.contact-status` badge whose id is `advisor-contact-status-${row.id}`. In the notes selector change handler, assign `row.status = status.value`, call `markDirty`, then call `updateAdvisorStatusBadge(row)` so unsaved notes content is not re-rendered or lost.

Style `.advisor-tab-signals` as a right-aligned compact column. Style `.contact-status` and its three state classes with the existing neutral, cyan, and success colors.

- [ ] **Step 4: Run the focused test and full suite**

Run:

```bash
pnpm test -- test/static.test.js -t "shows and immediately updates each advisor contact status in the curated index"
pnpm test
pnpm run check
```

Expected: both focused tests and all existing tests PASS; the Wrangler dry run exits successfully.

- [ ] **Step 5: Commit**

```bash
git add protected_phd_agent/test/static.test.js protected_phd_agent/public/app.js protected_phd_agent/public/style.css
git commit -m "feat: show advisor contact status in curated index"
```

### Task 3: Publish and verify

**Files:**
- No additional source files.

**Interfaces:**
- Consumes: the validated Worker project and its existing Wrangler configuration.
- Produces: a deployed version at the existing protected workflow URL and pushed commits on `main`.

- [ ] **Step 1: Review the final diff and repository status**

Run:

```bash
git diff --check
git status --short --branch
git log -3 --oneline
```

Expected: no whitespace errors; only intended commits differ from `origin/main`; unrelated user files are untouched.

- [ ] **Step 2: Deploy the validated project**

Run:

```bash
pnpm run deploy
```

Expected: Wrangler reports a successful deployment to the existing Worker.

- [ ] **Step 3: Push the committed changes**

```bash
git push origin main
```

Expected: `main` is pushed successfully.

- [ ] **Step 4: Perform fresh completion verification**

Run:

```bash
pnpm test
pnpm run check
git status --short --branch
```

Expected: 0 test failures, successful dry-run output, and `main...origin/main` with no task-related changes.
