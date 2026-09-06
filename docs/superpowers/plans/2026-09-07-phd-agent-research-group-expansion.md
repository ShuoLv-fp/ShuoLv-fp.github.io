# PhD Agent Research Group Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Research and append at least 100 verified, non-US, non-Canadian research-group leads to the protected PhD Application Agent without overwriting live user data.

**Architecture:** Add a narrowly scoped administrative faculty-append operation to the existing Cloudflare Durable Object and Worker router. Keep research records in an external private JSON batch, validate and deduplicate them locally and again against the authoritative cloud state, then deploy the code and submit the batch through a rotated secret without exposing private data or credentials.

**Tech Stack:** Cloudflare Workers, Durable Objects, Workers KV, JavaScript ES modules, Vitest Workers pool, Node.js standard library, Wrangler, official university/lab web sources.

## Global Constraints

- Append at least 100 valid new records after live deduplication; target 110–120 locally verified records for safety.
- Exclude groups whose primary institution is in the United States or Canada.
- Require at least one first-party institutional, lab, or official academic source per record.
- Do not create outreach-email artifacts for the new records.
- Do not overwrite existing faculty, notes, statuses, artifacts, rankings, or revisions.
- Keep the research batch, authenticated exports, production records, and all secret values outside the public Git repository.
- Assign positive `featured_rank` values after the current maximum so all new records appear in the existing dossier interface.
- Keep the current interface, navigation, search, and visual design unchanged.
- Use the existing `MIGRATION_SECRET` authorization boundary; never place its value in source, logs, screenshots, or command arguments.
- Preserve the existing package manager, lockfile, Cloudflare bindings, and production gateway URL.

---

## File Structure

- Create `protected_phd_agent/src/faculty-append.js`: pure record validation, normalization, forbidden-country enforcement, deduplication, and featured-rank assignment.
- Create `protected_phd_agent/test/faculty-append.test.js`: focused unit coverage for the pure append preparation logic.
- Modify `protected_phd_agent/src/coordinator.js`: secret-protected atomic append method and internal route handling.
- Modify `protected_phd_agent/src/worker.js`: explicitly allow only `POST /api/admin/faculty/append` in the public Worker router.
- Modify `protected_phd_agent/test/coordinator.test.js`: persistence, revision, preservation, and retry tests.
- Modify `protected_phd_agent/test/worker.test.js`: end-to-end authorization and route tests.
- Create `protected_phd_agent/scripts/validate_research_group_batch.mjs`: private-batch preflight that imports the production validator and prints aggregate counts only.
- Create `protected_phd_agent/scripts/append_research_group_batch.py`: secret-file or hidden-prompt HTTPS uploader that prints only the append result.
- Create `protected_phd_agent/test_py/test_research_group_batch_tools.py`: local tool tests with synthetic fixtures.
- Modify `docs/private-phd-agent-operations.md`: safe repeatable append, verification, recovery, and secret-rotation instructions.
- Create outside Git: `../ShuoLv-fp.github.io-private-agent-backup/research-group-expansion-2026-09-07.json`: verified production batch.

### Task 1: Pure faculty-batch validation and deduplication

**Files:**
- Create: `protected_phd_agent/src/faculty-append.js`
- Create: `protected_phd_agent/test/faculty-append.test.js`

**Interfaces:**
- Consumes: `existingRecords: FacultyRecord[]`, `submittedRecords: unknown`, `nowIso: string`.
- Produces: `prepareFacultyAppend(existingRecords, submittedRecords, nowIso): { appended: FacultyRecord[], skipped: number }`.
- Produces: `canonicalHttpUrl(value: string): string` for URL validation and normalized deduplication.

- [ ] **Step 1: Write failing validation tests**

Create tests using a fully synthetic valid record fixture. Cover valid preparation, rank allocation, HTTP(S) URL canonicalization, US/Canada rejection, empty and over-250 batches, missing required strings, invalid fit totals, missing first-party evidence, duplicate submitted IDs, existing ID collision, homepage deduplication, name-plus-institution deduplication, and idempotent resubmission.

The central happy-path assertion is:

```js
const result = prepareFacultyAppend([
  validFaculty({ id: "fac_existing", featured_rank: 28 })
], [
  validFaculty({
    id: "fac_0123456789ab",
    name: "Synthetic Researcher",
    display_name: "Synthetic Researcher",
    homepage_url: "https://example.edu/lab/",
    word_homepage_url: "https://example.edu/lab/"
  })
], "2026-09-07T00:00:00.000Z");

expect(result.skipped).toBe(0);
expect(result.appended).toHaveLength(1);
expect(result.appended[0].featured_rank).toBe(29);
expect(result.appended[0].status).toBe("discovered");
expect(result.appended[0].notes).toBe("");
expect(result.appended[0].updated_at).toBe("2026-09-07T00:00:00.000Z");
```

- [ ] **Step 2: Run the new test and confirm the missing-module failure**

Run: `cd protected_phd_agent && pnpm exec vitest run test/faculty-append.test.js`

Expected: FAIL because `../src/faculty-append.js` does not exist.

- [ ] **Step 3: Implement the pure validator**

Implement `faculty-append.js` with these exact boundaries:

```js
const MAX_BATCH = 250;
const FORBIDDEN_COUNTRIES = new Set([
  "canada", "ca", "united states", "united states of america", "usa", "us", "u.s.", "u.s.a."
]);
const REQUIRED_STRINGS = [
  "id", "name", "display_name", "institution", "institution_short", "department",
  "country", "region", "entry_type", "homepage_url", "word_homepage_url",
  "research_area", "research_summary", "email_addressee", "source_document"
];

export function canonicalHttpUrl(value) {
  const url = new URL(value);
  if (!new Set(["http:", "https:"]).has(url.protocol)) throw new Error("invalid HTTP(S) URL");
  url.hash = "";
  url.hostname = url.hostname.toLowerCase().replace(/^www\./, "");
  url.pathname = url.pathname.replace(/\/+$/, "") || "/";
  return url.href;
}

export function prepareFacultyAppend(existingRecords, submittedRecords, nowIso) {
  if (!Array.isArray(existingRecords)) throw new Error("invalid existing faculty");
  if (!Array.isArray(submittedRecords) || submittedRecords.length === 0) {
    throw new Error("faculty batch must be a non-empty array");
  }
  if (submittedRecords.length > MAX_BATCH) throw new Error("faculty batch too large");
  if (!Number.isFinite(Date.parse(nowIso))) throw new Error("invalid append timestamp");

  const clean = submittedRecords.map((record) => validateFacultyRecord(record, nowIso));
  const submittedIds = new Set();
  for (const record of clean) {
    if (submittedIds.has(record.id)) throw new Error("duplicate submitted faculty id");
    submittedIds.add(record.id);
  }

  const existingIds = new Map(existingRecords.map((record) => [record.id, record]));
  const homepages = new Set(existingRecords.map(homepageKey).filter(Boolean));
  const identities = new Set(existingRecords.map(identityKey));
  const appended = [];
  let skipped = 0;
  let nextRank = existingRecords.reduce(
    (maximum, record) => Math.max(maximum, Number(record.featured_rank) || 0),
    0
  );

  for (const record of clean) {
    const existingId = existingIds.get(record.id);
    const homepage = homepageKey(record);
    const identity = identityKey(record);
    if (existingId) {
      if (homepageKey(existingId) === homepage || identityKey(existingId) === identity) {
        skipped += 1;
        continue;
      }
      throw new Error("faculty id already exists");
    }
    if ((homepage && homepages.has(homepage)) || identities.has(identity)) {
      skipped += 1;
      continue;
    }
    nextRank += 1;
    const ranked = { ...record, featured_rank: nextRank };
    appended.push(ranked);
    existingIds.set(ranked.id, ranked);
    if (homepage) homepages.add(homepage);
    identities.add(identity);
  }
  return { appended, skipped };
}
```

Complete `validateFacultyRecord`, `homepageKey`, and `identityKey` in the same file. `validateFacultyRecord` must clone its input; require the listed strings; require IDs matching `^fac_[a-z0-9]{12,32}$`; reject forbidden normalized countries; validate both homepage URLs; require a non-empty keyword array; require at least one evidence item with non-empty `title`, `note`, and `checked_on` plus an HTTP(S) `url`; require `fit.total` to be an integer from 0 to 100, `fit.confidence` to be `low`, `medium`, or `high`, and `fit.dimensions` to be a non-empty array; require `match_analysis` to be a non-array object with non-empty `summary`; reject serialized records larger than 75,000 bytes; force `status: "discovered"`, `notes: ""`, `curated_on` from the date portion of `nowIso`, and `updated_at: nowIso`; and remove any submitted `featured_rank` before returning.

- [ ] **Step 4: Run the focused tests**

Run: `cd protected_phd_agent && pnpm exec vitest run test/faculty-append.test.js`

Expected: all faculty-append tests PASS.

- [ ] **Step 5: Commit the pure validation unit**

```bash
git add protected_phd_agent/src/faculty-append.js protected_phd_agent/test/faculty-append.test.js
git commit -m "feat: validate faculty expansion batches"
```

### Task 2: Atomic administrative append endpoint

**Files:**
- Modify: `protected_phd_agent/src/coordinator.js:1-200`
- Modify: `protected_phd_agent/src/worker.js:23-30`
- Modify: `protected_phd_agent/test/coordinator.test.js:57-116`
- Modify: `protected_phd_agent/test/worker.test.js:32-103`

**Interfaces:**
- Consumes: `prepareFacultyAppend` from Task 1.
- Produces: `WorkflowCoordinator.appendFaculty(records, migrationSecret): Promise<Response>`.
- Produces: `POST /api/admin/faculty/append` with body `{ "faculty": FacultyRecord[] }`.
- Success response: `{ revision, submitted, appended, skipped, previousFacultyTotal, facultyTotal, featuredTotal, artifactTotal }`.

- [ ] **Step 1: Write failing coordinator tests**

Add tests proving that the new method rejects the wrong secret, preserves every existing collection and existing record field, appends validated records in one revision, mirrors one KV snapshot, returns aggregate counts, and returns the same revision with `appended: 0` on an idempotent retry.

Use assertions equivalent to:

```js
const before = await (await coordinator.exportSnapshot()).json();
const response = await coordinator.appendFaculty(
  [validFaculty({ id: "fac_0123456789ab" })],
  "synthetic-migration-secret-32-bytes"
);
const result = await response.json();
const after = await (await coordinator.exportSnapshot()).json();

expect(result).toMatchObject({
  submitted: 1,
  appended: 1,
  skipped: 0,
  previousFacultyTotal: 1,
  facultyTotal: 2,
  artifactTotal: 1
});
expect(after.revision).toBe(before.revision + 1);
expect(after.artifacts).toEqual(before.artifacts);
expect(after.faculty[0]).toEqual(before.faculty[0]);
```

- [ ] **Step 2: Write failing Worker route tests**

Extend the synthetic Worker test to import its seed, submit the same one-record batch first with an incorrect bearer token and then with the test migration secret, and assert HTTP 403 followed by HTTP 200. Submit it a third time and assert `appended: 0`, `skipped: 1`. Confirm `GET`, `PUT`, and unauthenticated normal-session credentials cannot access this administrative route.

- [ ] **Step 3: Run the endpoint tests and confirm failure**

Run: `cd protected_phd_agent && pnpm exec vitest run test/coordinator.test.js test/worker.test.js`

Expected: FAIL because `appendFaculty` and the route do not exist.

- [ ] **Step 4: Implement the coordinator append operation**

Import `prepareFacultyAppend`. Add an `appendFaculty` method that verifies `MIGRATION_SECRET` with the existing constant-time comparison, rejects an uninitialized workflow, prepares the entire batch before modifying storage, returns HTTP 400 for validation failures, clones the current state only after validation, increments the revision exactly once when records are appended, persists the Durable Object state before the KV snapshot, and returns aggregate counts. When every submitted item is skipped, do not write storage and do not increment the revision.

Add route handling before normal session authentication:

```js
if (path === "/api/admin/faculty/append" && request.method === "POST") {
  if (!(request.headers.get("content-type") || "").toLowerCase().startsWith("application/json")) {
    return jsonResponse({ error: "JSON required" }, 415);
  }
  const authorization = request.headers.get("authorization") || "";
  const migrationSecret = authorization.startsWith("Bearer ")
    ? authorization.slice("Bearer ".length)
    : "";
  try {
    const body = await readJson(request, 10 * 1024 * 1024);
    return this.appendFaculty(body.faculty, migrationSecret);
  } catch (error) {
    return jsonResponse({ error: error.message }, 400);
  }
}
```

- [ ] **Step 5: Allow only the intended Worker method/path**

Update `isKnownApi` so `POST /api/admin/faculty/append` is forwarded and all other method/path combinations remain 404:

```js
if (path === "/api/logout" || path === "/api/admin/import" || path === "/api/admin/faculty/append") {
  return method === "POST";
}
```

- [ ] **Step 6: Run the endpoint and full JavaScript test suites**

Run: `cd protected_phd_agent && pnpm exec vitest run test/coordinator.test.js test/worker.test.js`

Expected: focused endpoint tests PASS.

Run: `cd protected_phd_agent && pnpm test`

Expected: all Worker tests PASS.

- [ ] **Step 7: Commit the atomic endpoint**

```bash
git add protected_phd_agent/src/coordinator.js protected_phd_agent/src/worker.js protected_phd_agent/test/coordinator.test.js protected_phd_agent/test/worker.test.js
git commit -m "feat: append private faculty records atomically"
```

### Task 3: Private-batch preflight and safe uploader

**Files:**
- Create: `protected_phd_agent/scripts/validate_research_group_batch.mjs`
- Create: `protected_phd_agent/scripts/append_research_group_batch.py`
- Create: `protected_phd_agent/test_py/test_research_group_batch_tools.py`

**Interfaces:**
- Consumes: external JSON `{ faculty: FacultyRecord[] }` and optional existing seed `{ faculty: FacultyRecord[] }`.
- Produces: aggregate preflight JSON containing `submitted`, `validNew`, `localDuplicates`, country counts, category counts, and score range; it never prints record bodies.
- Produces: authenticated POST uploader accepting `--batch`, `--url`, and either `--secret-file` or a hidden interactive prompt.

- [ ] **Step 1: Write failing tool tests with temporary synthetic data**

Test that the validator exits successfully for 100 valid unique synthetic non-US/non-Canadian records, fails below `--minimum`, fails on forbidden countries and malformed sources, and reports existing-seed duplicates without printing names. Test the uploader against a local HTTP test server, asserting the exact route, JSON body, bearer header presence, and aggregate response handling while ensuring the secret and record bodies are absent from stdout and stderr.

- [ ] **Step 2: Run the Python tool tests and confirm failure**

Run: `cd protected_phd_agent && python3 -m unittest test_py.test_research_group_batch_tools -v`

Expected: FAIL because both scripts are missing.

- [ ] **Step 3: Implement the Node preflight**

Use only `node:fs`, `node:path`, and `prepareFacultyAppend`. Parse `--batch`, `--existing`, and `--minimum`; reject paths inside the Git worktree by resolving the repository root and checking `path.relative`; load JSON; call `prepareFacultyAppend`; fail when `appended.length < minimum`; calculate aggregate country and category counts from the prepared records; print one JSON object with no names, URLs, summaries, or evidence text.

The accepted invocation is:

```bash
node scripts/validate_research_group_batch.mjs \
  --batch ../../ShuoLv-fp.github.io-private-agent-backup/research-group-expansion-2026-09-07.json \
  --existing ../../ShuoLv-fp.github.io-private-agent-backup/cloudflare-seed.json \
  --minimum 100
```

- [ ] **Step 4: Implement the HTTPS uploader**

Use only Python's standard library. Require an `https://` URL unless `--allow-http-localhost` is present for tests. Read the secret from a mode-0600 file or `getpass.getpass`, build the URL as `<base>/api/admin/faculty/append`, send the batch with `urllib.request`, cap the response read to 64 KiB, parse the aggregate JSON response, and print only `revision`, `submitted`, `appended`, `skipped`, `previousFacultyTotal`, `facultyTotal`, `featuredTotal`, and `artifactTotal`. Convert HTTP failures into a one-line status/error message without echoing request data or the bearer token.

- [ ] **Step 5: Run tool and full project tests**

Run: `cd protected_phd_agent && python3 -m unittest test_py.test_research_group_batch_tools -v`

Expected: all tool tests PASS.

Run: `cd protected_phd_agent && pnpm test && python3 -m unittest discover -s test_py -v`

Expected: all JavaScript and Python tests PASS.

- [ ] **Step 6: Commit the tools**

```bash
git add protected_phd_agent/scripts/validate_research_group_batch.mjs protected_phd_agent/scripts/append_research_group_batch.py protected_phd_agent/test_py/test_research_group_batch_tools.py
git commit -m "feat: add safe research batch operations"
```

### Task 4: Research and assemble the private faculty batch

**Files:**
- Create outside Git: `../ShuoLv-fp.github.io-private-agent-backup/research-group-expansion-2026-09-07.json`
- Read only: `../ShuoLv-fp.github.io-private-agent-backup/cloudflare-seed.json`
- Read only: `_pages/includes/pub.md`
- Read only: `_pages/includes/research_interests.md`

**Interfaces:**
- Consumes: the profile weights and existing faculty deduplication keys.
- Produces: `{ "faculty": FacultyRecord[] }` with at least 110 locally valid, first-party-sourced records.

- [ ] **Step 1: Build the discovery matrix**

Search current official sources across three independent lanes: Agent/AI4Science; computational and systems neuroscience; complex systems and interdisciplinary overlap. Target 140–160 plausible candidates across the eligible geographies. Record the official source URL, institution location, current research terms, and candidate category before scoring.

- [ ] **Step 2: Verify consequential facts from first-party sources**

For each retained candidate, confirm current institutional affiliation, PI or group-lead identity, research focus, and a working official URL. Use secondary sources only to discover candidates. Exclude entries supported only by search snippets, stale news articles, conference bios, rankings, or third-party directories.

- [ ] **Step 3: Deduplicate and score against Shuo's evidence base**

Compare normalized official URLs and name-plus-institution keys against the 93-record historical seed and within the candidate set. Score alignment using the fixed 45/35/20 profile weights. Write a concrete `match_analysis.summary` plus overlap and caution details tied to Shuo's LLM-agent/formal-reasoning work, cerebellar and individualized neuroimaging publications, visual-cortex work, or complex-contagion/network-dynamics research.

- [ ] **Step 4: Materialize the private batch**

Create the external JSON file with stable IDs derived from a SHA-256 digest of normalized name, institution, and official URL, using the first 12 lowercase hexadecimal characters after the `fac_` prefix. Include all required fields, at least one evidence record, `fit.total`, `fit.confidence`, and non-empty `fit.dimensions`. Do not include artifacts or email drafts. Do not place the batch in the repository or staging area.

- [ ] **Step 5: Run the private-batch preflight**

Run:

```bash
cd protected_phd_agent
node scripts/validate_research_group_batch.mjs \
  --batch ../../ShuoLv-fp.github.io-private-agent-backup/research-group-expansion-2026-09-07.json \
  --existing ../../ShuoLv-fp.github.io-private-agent-backup/cloudflare-seed.json \
  --minimum 100
```

Expected: exit 0; `validNew` is at least 100; forbidden-country count is zero; minimum and maximum scores are within 0–100; no record content is printed.

- [ ] **Step 6: Independently spot-check the highest-impact records**

Re-open official sources for at least the ten highest-scoring records and a geographically diverse sample of ten additional records. Resolve affiliation, scope, or URL discrepancies before deployment. Stop discovery once at least 110 strong records pass validation and further searches are producing mostly duplicates or weaker matches.

### Task 5: Document and verify the operational workflow

**Files:**
- Modify: `docs/private-phd-agent-operations.md:23-83`

**Interfaces:**
- Consumes: the preflight and uploader commands from Task 3.
- Produces: a safe runbook for future append batches and rollback.

- [ ] **Step 1: Add the append runbook**

Document the external batch location rule, preflight command, `MIGRATION_SECRET` rotation, secure temporary secret-file lifecycle, deployment order, uploader invocation, idempotent retry semantics, aggregate-only verification, and the fact that the route never overwrites existing records.

Use this operational sequence:

```bash
cd protected_phd_agent
secret_file="$(mktemp)"
chmod 600 "$secret_file"
openssl rand -hex 32 -out "$secret_file"
pnpm exec wrangler secret put MIGRATION_SECRET < "$secret_file"
python3 scripts/append_research_group_batch.py \
  --url https://shuo-phd-agent-gateway.pages.dev \
  --batch ../../ShuoLv-fp.github.io-private-agent-backup/research-group-expansion-2026-09-07.json \
  --secret-file "$secret_file"
rm -f "$secret_file"
unset secret_file
```

State that the exact temporary path returned by `mktemp` must be used, the file must be removed immediately after the append, and a failed append can be retried safely with the same batch.

- [ ] **Step 2: Check documentation and repository privacy**

Run: `git diff --check`

Expected: no whitespace errors.

Run: `git status --short --ignored`

Expected: the production research batch is absent from tracked and untracked repository files.

- [ ] **Step 3: Commit the runbook**

```bash
git add docs/private-phd-agent-operations.md
git commit -m "docs: document private faculty expansion"
```

### Task 6: Deploy, append, and verify production

**Files:**
- Read only: `protected_phd_agent/wrangler.jsonc`
- Read only: external private batch and generated temporary secret file.

**Interfaces:**
- Consumes: deployed append route and validated private batch.
- Produces: a live aggregate result proving at least 100 new records were appended.

- [ ] **Step 1: Run final local verification**

Run: `cd protected_phd_agent && pnpm test && python3 -m unittest discover -s test_py -v && pnpm run check`

Expected: every JavaScript and Python test passes, and the Wrangler dry run succeeds.

- [ ] **Step 2: Confirm Cloudflare identity and deploy**

Run: `cd protected_phd_agent && pnpm exec wrangler whoami`

Expected: authenticated account information for the existing deployment.

Run: `cd protected_phd_agent && pnpm exec wrangler deploy`

Expected: successful deployment of `shuo-phd-agent` with the existing Durable Object and KV bindings.

- [ ] **Step 3: Verify the unauthenticated boundary**

Run: `curl --silent --output /dev/null --write-out '%{http_code}\n' https://shuo-phd-agent-gateway.pages.dev/api/bootstrap`

Expected: `401`.

Run: `curl --silent --output /dev/null --write-out '%{http_code}\n' -X GET https://shuo-phd-agent-gateway.pages.dev/api/admin/faculty/append`

Expected: `404`.

- [ ] **Step 4: Rotate the migration secret and append the batch**

Create a mode-0600 temporary secret file with `mktemp` and `openssl rand -hex 32 -out`, install it using `wrangler secret put MIGRATION_SECRET` through standard input, and call `append_research_group_batch.py` with the production gateway, external batch, and secret-file path. Remove only that exact temporary file immediately afterward.

Expected uploader output: `appended` is at least 100, `facultyTotal` increased by the same amount, `featuredTotal` increased by the same amount, and no record content or secret is printed.

- [ ] **Step 5: Prove idempotence and preservation**

Submit the same batch a second time before removing the temporary secret file.

Expected: `appended: 0`, `skipped` equals the submitted batch count, and `revision` is unchanged from the first response.

Confirm `facultyTotal - appended` equals `previousFacultyTotal`, `artifactTotal` is unchanged on retry, and the idempotent response preserves `facultyTotal`, `featuredTotal`, and `revision`. If fewer than 100 records were appended because live data contained more duplicates than the historical seed, research and validate a supplemental external batch, append it, and repeat until the cumulative appended count is at least 100.

- [ ] **Step 6: Verify live availability and repository cleanliness**

Confirm the protected `/app` route still returns 401 without a session and the login shell returns 200. Confirm the append endpoint rejects the now-removed secret material by ensuring the temporary file no longer exists; do not intentionally submit a secret after deletion. Run `git status --short` and verify no production JSON or secret file appears.

- [ ] **Step 7: Record final aggregate results without private data**

Summarize submitted, appended, skipped, final faculty total, final featured total, score range, counts by country, and counts by research category. Include only official source links needed to support the research methodology or representative highest-fit selections; do not publish the private batch or full dossier text.

### Task 7: Final review and completion commit

**Files:**
- Review: all files changed by Tasks 1–6.

**Interfaces:**
- Consumes: completed implementation, passing tests, production aggregate response, and clean repository status.
- Produces: a reviewed branch ready for the user's normal GitHub workflow.

- [ ] **Step 1: Review the complete diff**

Run: `git diff HEAD~4 -- protected_phd_agent docs/private-phd-agent-operations.md`

Expected: only the append validator, protected route, tests, safe tools, and operations documentation are present; no production research records or secret values appear.

- [ ] **Step 2: Search for privacy regressions**

Run:

```bash
git ls-files | rg 'research-group-expansion.*\.json|private_data|cloudflare-seed' && exit 1 || true
git grep -n 'Authorization: Bearer [A-Za-z0-9]' -- protected_phd_agent docs && exit 1 || true
```

Expected: both checks exit successfully with no matches containing production files or literal bearer values.

- [ ] **Step 3: Re-run the complete verification suite**

Run: `cd protected_phd_agent && pnpm test && python3 -m unittest discover -s test_py -v && pnpm run check`

Expected: all tests and the deployment dry run PASS.

- [ ] **Step 4: Commit any final reviewed documentation-only correction**

If the diff review required a correction, commit only that correction:

```bash
git add protected_phd_agent docs/private-phd-agent-operations.md
git commit -m "chore: finalize faculty expansion workflow"
```

If no correction was required, do not create an empty commit.
