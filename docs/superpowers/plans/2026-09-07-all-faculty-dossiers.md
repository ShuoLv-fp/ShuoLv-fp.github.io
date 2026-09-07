# All Faculty Dossiers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display all 238 production faculty records in the existing dossier list while keeping the original 28 featured records first.

**Architecture:** Add a small pure browser-side ordering module, then make the dossier view consume its ordered copy of `state.faculty`. Serve the new module through the existing authenticated asset gate; no backend data or schema changes are required.

**Tech Stack:** Vanilla JavaScript ES modules, Cloudflare Workers static assets, Vitest, `@cloudflare/vitest-pool-workers`, Wrangler.

## Global Constraints

- Show every faculty record already returned by `/api/bootstrap`.
- Sort positive `featured_rank` values first in ascending order.
- Sort remaining records by descending `fit.total`, then display name and institution.
- Preserve search, dossier detail, status editing, drafts, cloud synchronization, and all production data.
- Keep the new JavaScript asset inaccessible before authentication.
- Work directly on `main`, as approved by the user, while preserving unrelated commits and changes.

---

### Task 1: Pure faculty ordering

**Files:**
- Create: `protected_phd_agent/public/faculty-list.js`
- Create: `protected_phd_agent/test/faculty-list.test.js`

**Interfaces:**
- Consumes: `Array<object>` faculty records from the bootstrap state.
- Produces: `orderFaculty(records): Array<object>`, a new ordered array that does not mutate its input.

- [ ] **Step 1: Write the failing ordering tests**

```js
import { describe, expect, it } from "vitest";
import { orderFaculty } from "../public/faculty-list.js";

describe("orderFaculty", () => {
  it("shows every record with featured faculty first and the rest by fit", () => {
    const records = [
      { id: "plain-low", name: "Alpha", fit: { total: 82 } },
      { id: "featured-two", name: "Delta", featured_rank: 2, fit: { total: 99 } },
      { id: "plain-high", name: "Beta", fit: { total: 98 } },
      { id: "featured-one", name: "Gamma", featured_rank: 1, fit: { total: 80 } }
    ];

    expect(orderFaculty(records).map((record) => record.id)).toEqual([
      "featured-one", "featured-two", "plain-high", "plain-low"
    ]);
    expect(records.map((record) => record.id)).toEqual([
      "plain-low", "featured-two", "plain-high", "featured-one"
    ]);
  });

  it("uses display name and institution as deterministic tie breakers", () => {
    const records = [
      { id: "z", display_name: "Same", institution: "Zurich", fit: { total: 90 } },
      { id: "b", display_name: "Beta", institution: "Berlin", fit: { total: 90 } },
      { id: "a", display_name: "Same", institution: "Amsterdam", fit: { total: 90 } }
    ];

    expect(orderFaculty(records).map((record) => record.id)).toEqual(["b", "a", "z"]);
  });
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```sh
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
  pnpm --dir protected_phd_agent exec vitest run test/faculty-list.test.js
```

Expected: FAIL because `public/faculty-list.js` does not exist.

- [ ] **Step 3: Implement the minimal pure ordering module**

```js
function positiveRank(record) {
  const rank = Number(record?.featured_rank);
  return Number.isFinite(rank) && rank > 0 ? rank : null;
}

function fitScore(record) {
  const score = Number(record?.fit?.total);
  return Number.isFinite(score) ? score : -1;
}

function text(value) {
  return String(value || "").trim();
}

export function orderFaculty(records) {
  if (!Array.isArray(records)) return [];
  return [...records].sort((left, right) => {
    const leftRank = positiveRank(left);
    const rightRank = positiveRank(right);
    if (leftRank !== null || rightRank !== null) {
      if (leftRank === null) return 1;
      if (rightRank === null) return -1;
      if (leftRank !== rightRank) return leftRank - rightRank;
    }

    const scoreDifference = fitScore(right) - fitScore(left);
    if (scoreDifference) return scoreDifference;
    const nameDifference = text(left?.display_name || left?.name)
      .localeCompare(text(right?.display_name || right?.name), "en", { sensitivity: "base" });
    if (nameDifference) return nameDifference;
    return text(left?.institution)
      .localeCompare(text(right?.institution), "en", { sensitivity: "base" });
  });
}
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the Step 2 command again.

Expected: 2 tests pass.

- [ ] **Step 5: Commit the ordering unit**

```sh
git add protected_phd_agent/public/faculty-list.js protected_phd_agent/test/faculty-list.test.js
git commit -m "feat: order complete faculty dossier list"
```

---

### Task 2: Connect the complete list to the protected UI

**Files:**
- Modify: `protected_phd_agent/public/app.js`
- Modify: `protected_phd_agent/public/index.html`
- Modify: `protected_phd_agent/src/worker.js`
- Modify: `protected_phd_agent/test/static.test.js`
- Modify: `protected_phd_agent/test/worker.test.js`

**Interfaces:**
- Consumes: `orderFaculty(records)` from Task 1.
- Produces: an authenticated dossier view containing every faculty record and an authenticated `/faculty-list.js` asset route.

- [ ] **Step 1: Write failing integration assertions**

Update `uiSources()` in `test/static.test.js` to fetch `/faculty-list.js` with the authenticated cookie and return its body as `facultyListJs`. Add assertions that `app.js` imports `orderFaculty`, calls `orderFaculty(state.faculty)`, does not filter on `featured_rank`, and that the HTML contains `ADVISOR INDEX`. In `test/worker.test.js`, add `/faculty-list.js` to the protected pre-login checks and assert it returns `200` after login.

```js
expect((await SELF.fetch(`${origin}/faculty-list.js`)).status).toBe(401);
expect((await SELF.fetch(`${origin}/faculty-list.js`, { headers: { cookie } })).status).toBe(200);
expect(appJs).toContain('import { orderFaculty } from "./faculty-list.js";');
expect(appJs).toContain("return orderFaculty(state.faculty);");
expect(appJs).not.toContain(".filter((row) => Number(row.featured_rank) > 0)");
expect(html).toContain("ADVISOR INDEX");
expect(facultyListJs).toContain("export function orderFaculty(records)");
```

- [ ] **Step 2: Run integration tests and verify RED**

Run:

```sh
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
  pnpm --dir protected_phd_agent exec vitest run test/static.test.js test/worker.test.js
```

Expected: FAIL because the helper is not served and `app.js` still filters to featured records.

- [ ] **Step 3: Connect the ordering module and protect its route**

At the top of `public/app.js`:

```js
import { orderFaculty } from "./faculty-list.js";
```

Replace `dossierRows()` with:

```js
function dossierRows() {
  return orderFaculty(state.faculty);
}
```

Change the dashboard metric label from `Curated advisors` to `Advisor records`, and change `CURATED INDEX` in `public/index.html` to `ADVISOR INDEX`. In `src/worker.js`, add `/faculty-list.js` beside `/app.js` in the authenticated protected-asset condition.

- [ ] **Step 4: Run integration tests and the full suite**

Run:

```sh
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
  pnpm --dir protected_phd_agent test -- --run
```

Expected: all JavaScript tests pass.

- [ ] **Step 5: Commit the UI integration**

```sh
git add protected_phd_agent/public/app.js protected_phd_agent/public/index.html \
  protected_phd_agent/src/worker.js protected_phd_agent/test/static.test.js \
  protected_phd_agent/test/worker.test.js
git commit -m "fix: show every faculty dossier"
```

---

### Task 3: Verify and deploy

**Files:**
- No production file changes expected.

**Interfaces:**
- Consumes: the tested Worker bundle from Tasks 1 and 2.
- Produces: a deployed UI that renders 238 advisor dossiers with 28 featured records first.

- [ ] **Step 1: Run complete local verification**

```sh
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
NODE_BINARY=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  pnpm --dir protected_phd_agent check
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
NODE_BINARY=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  python3 -m unittest discover -s protected_phd_agent/test_py -t . -v
```

Expected: all JavaScript and Python tests pass and Wrangler's production dry run exits successfully.

- [ ] **Step 2: Deploy the Worker**

```sh
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
NODE_BINARY=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  pnpm --dir protected_phd_agent deploy
```

Expected: Wrangler reports the `shuo-phd-agent` Worker deployed successfully.

- [ ] **Step 3: Verify production aggregates without printing private records**

```sh
set -o pipefail
PATH=/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
  pnpm --dir protected_phd_agent exec wrangler kv key get \
  --binding PHD_AGENT_DATA --remote snapshot:latest | \
python3 -c 'import json,sys; d=json.load(sys.stdin); f=d["faculty"]; print({"facultyTotal":len(f),"featuredTotal":sum(1 for x in f if int(x.get("featured_rank",0) or 0)>0),"artifactTotal":len(d["artifacts"])})'
```

Expected: `facultyTotal` is 238, `featuredTotal` is 28, and `artifactTotal` is 28.

- [ ] **Step 4: Push the approved direct-main commits**

```sh
git fetch origin main
git rev-list --left-right --count origin/main...main
git push origin main
git status --short
```

Expected: the push is non-forced, `origin/main...main` has no remote-only commits before pushing, and the final working tree is clean.
