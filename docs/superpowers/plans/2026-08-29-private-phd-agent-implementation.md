# Private Cloud PhD Application Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the PhD Application Agent as a password-protected Cloudflare Worker, move all production workflow data into private Cloudflare storage, expose a cloud-sync editing flow, link the English and Chinese homepage Lean icons to it, and remove the old plaintext workflow from public Git history.

**Architecture:** A Cloudflare Worker serves a data-free vanilla frontend and guards every workflow/API route. A single `WorkflowCoordinator` Durable Object provides strongly ordered state and revision checks; Workers KV stores versioned recovery snapshots. The public GitHub repository retains only program code and synthetic fixtures, while current production JSON is backed up locally, imported through a one-time secret-protected route, and then removed from all public Git refs.

**Tech Stack:** Cloudflare Workers static assets, Durable Objects with SQLite-backed storage, Workers KV, Wrangler 4.45+, JavaScript ES modules, Vitest Workers pool, vanilla HTML/CSS/JavaScript, Python 3 standard library migration tools, Jekyll, GitHub Pages, `git-filter-repo` 2.47+.

**Approved Design:** `docs/superpowers/specs/2026-08-29-phd-agent-private-cloud-design.md`

## Global Constraints

- Keep `https://shuolv-fp.github.io/` as the public Jekyll homepage.
- Deploy the protected workflow to the Cloudflare-generated `workers.dev` URL for the `shuo-phd-agent` Worker.
- Only the Lean image links to the protected workflow; the adjacent Lean text continues linking to `https://lean-lang.org/`.
- Never place the user-selected workflow password, `SESSION_SECRET`, `RATE_LIMIT_SECRET`, or `MIGRATION_SECRET` in Git, browser storage, logs, fixtures, screenshots, or build output.
- Require `HttpOnly`, `Secure`, `SameSite=Strict` sessions with twelve-hour expiry.
- Lock login for 15 minutes after five failed attempts within 15 minutes.
- Require a same-origin request and session-bound CSRF token for every mutation.
- Serialize all production reads and writes through one Durable Object; use KV only for recovery snapshots and authenticated exports.
- Reject stale revisions with HTTP 409 and never silently overwrite newer cloud state.
- Store current plaintext data only in the ignored local path `phd_application_agent/private_data/` during migration.
- Keep production data out of the public Worker assets and synthetic tests.
- Preserve draft-only outreach; do not add SMTP, send-mail, webhook, arbitrary proxy, or generic file-write endpoints.
- Do not start Git history rewriting until local backup, Git bundle, Cloudflare import, authenticated readback, and record-count/hash validation all pass.
- Rewrite public history with `git-filter-repo --sensitive-data-removal`, then force-update only after rechecking the remote head.
- Treat history removal as best effort for the repository's refs; independent clones, forks, and third-party caches cannot be erased by this workflow.

---

## File Map

| Path | Responsibility |
|---|---|
| `protected_phd_agent/wrangler.jsonc` | Worker, static assets, KV auto-provisioning, Durable Object migration |
| `protected_phd_agent/package.json` | Wrangler and Vitest commands/dependencies |
| `protected_phd_agent/vitest.config.js` | Workers test pool with synthetic secrets |
| `protected_phd_agent/test/support/memory-storage.js` | Deterministic storage double for auth unit tests |
| `protected_phd_agent/src/http.js` | JSON responses, cookie parsing, security headers, body limits |
| `protected_phd_agent/src/auth.js` | Password comparison, rate limiting, sessions, CSRF |
| `protected_phd_agent/src/coordinator.js` | Authoritative workflow state, revision checks, snapshot mirroring |
| `protected_phd_agent/src/validation.js` | Collection/field/type/size allowlists |
| `protected_phd_agent/src/worker.js` | Route dispatch, asset gate, API composition, one-time import |
| `protected_phd_agent/public/index.html` | Authenticated application shell without production data |
| `protected_phd_agent/public/login.html` | Unauthenticated password form only |
| `protected_phd_agent/public/login.js` | Password submission and redirect without persistent secrets |
| `protected_phd_agent/public/app.js` | Login, bootstrap, dossier rendering, dirty state, sync, conflict/export/logout |
| `protected_phd_agent/public/style.css` | Existing dossier visual system plus login/sync states |
| `protected_phd_agent/public/logos/*.svg` | Data-free local institution marks |
| `protected_phd_agent/test/*.test.js` | Auth, coordinator, API, static and secret-leak tests |
| `protected_phd_agent/scripts/prepare_private_migration.py` | Local backup, seed bundle, manifest and public-leak term hashes |
| `protected_phd_agent/scripts/verify_private_migration.py` | Count/hash verification without printing sensitive content |
| `protected_phd_agent/scripts/verify_rewritten_history.py` | Scan all reachable refs for removed paths and sampled private strings |
| `tests/test_phd_agent_entry.py` | Jekyll Lean-icon link and exclusion checks |
| `_config.yml` | Protected workflow URL and Jekyll exclusions |
| `_pages/includes/technical_skills.md` | English Lean-image entry |
| `_pages/includes/zh/technical_skills.md` | Chinese Lean-image entry |
| `.gitignore` | Prevent old local workflow and private data from being recommitted |
| `docs/private-phd-agent-operations.md` | Deployment, secret rotation, backup, restore and history-cleanup runbook |

---

### Task 1: Create the Cloudflare project and test harness

**Files:**
- Modify: `.gitignore`
- Create: `protected_phd_agent/package.json`
- Create: `protected_phd_agent/wrangler.jsonc`
- Create: `protected_phd_agent/vitest.config.js`
- Create: `protected_phd_agent/src/http.js`
- Create: `protected_phd_agent/src/worker.js`
- Create: `protected_phd_agent/public/login.html`
- Create: `protected_phd_agent/test/http.test.js`

**Interfaces:**
- Produces: `jsonResponse(payload, status?, extraHeaders?) -> Response`
- Produces: `secureHeaders() -> Headers`
- Produces: `readJson(request, maxBytes?) -> Promise<object>`
- Produces bindings: `PHD_AGENT_DATA: KVNamespace`, `WORKFLOW_COORDINATOR: DurableObjectNamespace`, `ASSETS: Fetcher`

- [ ] **Step 1: Add the package and Worker configuration**

Before installing dependencies or starting local development, add these generated local paths to the root `.gitignore`:

```gitignore
protected_phd_agent/.dev.vars
protected_phd_agent/.wrangler/
```

```json
{
  "name": "shuo-private-phd-agent",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@11.19.0",
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "check": "vitest run && wrangler deploy --dry-run"
  },
  "devDependencies": {
    "@cloudflare/vitest-pool-workers": "0.22.0",
    "vitest": "4.1.11",
    "wrangler": "4.127.1"
  }
}
```

Create `vitest.config.js` with `defineWorkersConfig({ test: { poolOptions: { workers: { wrangler: { configPath: "./wrangler.jsonc" } } } } })`. Create a minimal data-free `public/login.html` and a temporary `src/worker.js` that returns JSON status 503 for every route through `jsonResponse`; Task 4 replaces this temporary route behavior after its failing tests exist.

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "shuo-phd-agent",
  "main": "src/worker.js",
  "compatibility_date": "2026-08-29",
  "assets": {
    "directory": "./public",
    "binding": "ASSETS",
    "run_worker_first": true
  },
  "kv_namespaces": [{ "binding": "PHD_AGENT_DATA" }],
  "durable_objects": {
    "bindings": [{ "name": "WORKFLOW_COORDINATOR", "class_name": "WorkflowCoordinator" }]
  },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["WorkflowCoordinator"] }]
}
```

- [ ] **Step 2: Write failing HTTP helper tests**

```js
import { describe, expect, it } from "vitest";
import { jsonResponse, readJson, secureHeaders } from "../src/http.js";

describe("HTTP boundary", () => {
  it("adds restrictive response headers", () => {
    const headers = secureHeaders();
    expect(headers.get("content-security-policy")).toContain("default-src 'self'");
    expect(headers.get("x-content-type-options")).toBe("nosniff");
    expect(headers.get("referrer-policy")).toBe("no-referrer");
  });

  it("rejects JSON bodies larger than the configured limit", async () => {
    const request = new Request("https://agent.test/api", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ value: "x".repeat(100) })
    });
    await expect(readJson(request, 32)).rejects.toThrow("request body too large");
  });

  it("serializes JSON without reflecting secrets into headers", async () => {
    const response = jsonResponse({ ok: true }, 201);
    expect(response.status).toBe(201);
    expect(await response.json()).toEqual({ ok: true });
  });
});
```

- [ ] **Step 3: Run the test and confirm RED**

Run: `cd protected_phd_agent && pnpm install && pnpm test -- test/http.test.js`

Expected: FAIL because `src/http.js` does not exist.

- [ ] **Step 4: Implement the minimal HTTP boundary**

```js
export function secureHeaders() {
  return new Headers({
    "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store"
  });
}

export function jsonResponse(payload, status = 200, extraHeaders = {}) {
  const headers = secureHeaders();
  headers.set("Content-Type", "application/json; charset=utf-8");
  for (const [key, value] of Object.entries(extraHeaders)) headers.set(key, value);
  return new Response(JSON.stringify(payload), { status, headers });
}

export async function readJson(request, maxBytes = 1_048_576) {
  const length = Number(request.headers.get("content-length") || 0);
  if (length > maxBytes) throw new Error("request body too large");
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > maxBytes) throw new Error("request body too large");
  const value = JSON.parse(text);
  if (!value || Array.isArray(value) || typeof value !== "object") throw new Error("expected JSON object");
  return value;
}
```

- [ ] **Step 5: Verify GREEN and commit**

Run: `cd protected_phd_agent && pnpm test -- test/http.test.js`

Expected: all HTTP tests pass.

```bash
git add .gitignore protected_phd_agent/package.json protected_phd_agent/pnpm-lock.yaml protected_phd_agent/wrangler.jsonc protected_phd_agent/vitest.config.js protected_phd_agent/src/http.js protected_phd_agent/src/worker.js protected_phd_agent/public/login.html protected_phd_agent/test/http.test.js
git commit -m "feat: scaffold protected PhD agent worker"
```

---

### Task 2: Implement password authentication, sessions, lockout and CSRF

**Files:**
- Create: `protected_phd_agent/src/auth.js`
- Create: `protected_phd_agent/test/auth.test.js`
- Modify: `protected_phd_agent/vitest.config.js`

**Interfaces:**
- Consumes: a Durable Object storage-compatible object with `get`, `put`, and `delete`
- Produces: `authenticate(request, env, storage) -> Promise<{sessionId, csrf, expiresAt} | null>`
- Produces: `login(request, env, storage) -> Promise<Response>`
- Produces: `logout(request, env, storage) -> Promise<Response>`
- Produces: `requireMutationGuards(request, session, expectedOrigin) -> boolean`

- [ ] **Step 1: Configure synthetic test-only secrets**

```js
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.jsonc" },
        miniflare: {
          bindings: {
            WORKFLOW_PASSWORD: "synthetic-test-password",
            SESSION_SECRET: "synthetic-session-secret-with-32-bytes",
            RATE_LIMIT_SECRET: "synthetic-rate-limit-secret-32-bytes",
            MIGRATION_SECRET: "synthetic-migration-secret-32-bytes"
          }
        }
      }
    }
  }
});
```

- [ ] **Step 2: Write failing authentication tests**

```js
import { describe, expect, it } from "vitest";
import { createMemoryStorage } from "./support/memory-storage.js";
import { authenticate, login, logout, requireMutationGuards } from "../src/auth.js";

const env = {
  WORKFLOW_PASSWORD: "synthetic-test-password",
  SESSION_SECRET: "synthetic-session-secret-with-32-bytes",
  RATE_LIMIT_SECRET: "synthetic-rate-limit-secret-32-bytes"
};

describe("authentication", () => {
  it("issues a secure twelve-hour session for the correct password", async () => {
    const storage = createMemoryStorage();
    const request = new Request("https://agent.test/api/login", {
      method: "POST",
      headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.9" },
      body: JSON.stringify({ password: "synthetic-test-password" })
    });
    const response = await login(request, env, storage);
    expect(response.status).toBe(200);
    const cookie = response.headers.get("set-cookie");
    expect(cookie).toContain("HttpOnly");
    expect(cookie).toContain("Secure");
    expect(cookie).toContain("SameSite=Strict");
  });

  it("locks after five failed attempts", async () => {
    const storage = createMemoryStorage();
    for (let attempt = 0; attempt < 5; attempt += 1) {
      await login(new Request("https://agent.test/api/login", {
        method: "POST",
        headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.10" },
        body: JSON.stringify({ password: "wrong" })
      }), env, storage);
    }
    const blocked = await login(new Request("https://agent.test/api/login", {
      method: "POST",
      headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.10" },
      body: JSON.stringify({ password: "synthetic-test-password" })
    }), env, storage);
    expect(blocked.status).toBe(429);
  });

  it("requires matching origin and CSRF for a mutation", () => {
    const request = new Request("https://agent.test/api/artifacts/a1", {
      method: "PUT",
      headers: { origin: "https://agent.test", "x-csrf-token": "csrf-1" }
    });
    expect(requireMutationGuards(request, { csrf: "csrf-1" }, "https://agent.test")).toBe(true);
  });
});
```

- [ ] **Step 3: Run the test and confirm RED**

Run: `cd protected_phd_agent && pnpm test -- test/auth.test.js`

Expected: FAIL because `src/auth.js` and the memory storage support module do not exist.

- [ ] **Step 4: Implement authentication with Web Crypto and server-side session records**

Implement these exact policies in `src/auth.js`:

Export `SESSION_TTL_SECONDS = 43200`, `LOCK_WINDOW_SECONDS = 900`, and `MAX_FAILURES = 5`. Implement `authenticate(request, env, storage)`, `login(request, env, storage)`, `logout(request, env, storage)`, and `requireMutationGuards(request, session, expectedOrigin)` with the signatures defined above. The implementation must use `crypto.subtle` HMAC-SHA-256, `crypto.randomUUID()`, and constant-time byte comparison. Storage keys are `session:${uuid}` and `rate:${hmacOfClientAddress}`; raw client addresses are never stored. `requireMutationGuards` returns true only when the request origin equals the URL origin and `x-csrf-token` equals the session CSRF value. These storage-taking functions execute inside the singleton coordinator so all rate and session changes are serialized.

- [ ] **Step 5: Verify GREEN and commit**

Run: `cd protected_phd_agent && pnpm test -- test/auth.test.js && pnpm test`

Expected: authentication tests and the existing suite pass.

```bash
git add protected_phd_agent/src/auth.js protected_phd_agent/test/auth.test.js protected_phd_agent/test/support/memory-storage.js protected_phd_agent/vitest.config.js
git commit -m "feat: protect PhD agent sessions"
```

---

### Task 3: Implement strongly ordered workflow state and recovery snapshots

**Files:**
- Create: `protected_phd_agent/src/validation.js`
- Create: `protected_phd_agent/src/coordinator.js`
- Create: `protected_phd_agent/test/coordinator.test.js`
- Modify: `protected_phd_agent/src/worker.js`

**Interfaces:**
- Produces: `validatePatch(collection, patch) -> object`
- Produces Durable Object RPC methods: `bootstrap()`, `update(collection, id, patch, expectedRevision)`, `importOnce(seed, migrationSecret)`, `exportSnapshot()`
- State schema: `{schemaVersion: 1, revision: number, updatedAt: string, profile: object, faculty: object[], programs: object[], applications: object[], artifacts: object[]}`

- [ ] **Step 1: Write failing validation and revision tests**

```js
import { describe, expect, it } from "vitest";
import { validatePatch } from "../src/validation.js";

describe("workflow mutation schema", () => {
  it("allows only editable outreach fields", () => {
    expect(validatePatch("artifacts", { subject: "Revised", content: "Body", status: "draft" }))
      .toEqual({ subject: "Revised", content: "Body", status: "draft" });
    expect(() => validatePatch("artifacts", { target_id: "rewire-target" })).toThrow("field not editable");
  });

  it("rejects oversized email bodies", () => {
    expect(() => validatePatch("artifacts", { content: "x".repeat(50_001) })).toThrow("field too large");
  });
});
```

Add a coordinator integration test that imports a synthetic record, updates revision `1`, verifies revision `2`, and confirms a second update with expected revision `1` returns status 409 without changing the subject.

- [ ] **Step 2: Run the test and confirm RED**

Run: `cd protected_phd_agent && pnpm test -- test/coordinator.test.js`

Expected: FAIL because the validation and coordinator modules do not exist.

- [ ] **Step 3: Implement explicit collection allowlists**

```js
const RULES = {
  faculty: {
    notes: { type: "string", max: 20_000 },
    status: { type: "string", choices: ["discovered", "shortlisted", "contacted"] },
    match_analysis: { type: "object", max: 50_000 }
  },
  artifacts: {
    subject: { type: "string", max: 1_000 },
    content: { type: "string", max: 50_000 },
    status: { type: "string", choices: ["draft", "reviewed"] },
    review_note: { type: "string", max: 10_000 },
    planned_send_date: { type: "string", max: 32 },
    follow_up_date: { type: "string", max: 32 },
    requires_human_review: { type: "boolean" }
  }
};
```

`validatePatch` rejects unknown collections, unknown fields, wrong types, disallowed choices, and serialized values above the maximum.

- [ ] **Step 4: Implement `WorkflowCoordinator`**

The class exports from `src/coordinator.js`, stores the authoritative state under Durable Object storage key `workflow`, increments one global revision per accepted mutation, and calls `env.PHD_AGENT_DATA.put("snapshot:latest", JSON.stringify(state))` after each import or update. `importOnce` succeeds only when storage key `migration_complete` is absent and the supplied bearer secret matches `env.MIGRATION_SECRET` using constant-time comparison. `src/worker.js` re-exports it with `export { WorkflowCoordinator } from "./coordinator.js";` so the Wrangler `class_name` resolves from the configured main module.

- [ ] **Step 5: Verify RED-GREEN and commit**

Run: `cd protected_phd_agent && pnpm test -- test/coordinator.test.js && pnpm test`

Expected: schema, import, revision, conflict and KV mirror tests pass.

```bash
git add protected_phd_agent/src/validation.js protected_phd_agent/src/coordinator.js protected_phd_agent/src/worker.js protected_phd_agent/test/coordinator.test.js
git commit -m "feat: add versioned private workflow store"
```

---

### Task 4: Compose the protected Worker API and asset gate

**Files:**
- Modify: `protected_phd_agent/src/worker.js`
- Create: `protected_phd_agent/test/worker.test.js`
- Modify: `protected_phd_agent/public/login.html`
- Create: `protected_phd_agent/public/login.js`
- Create: `protected_phd_agent/public/index.html`

**Interfaces:**
- Consumes: auth helpers and the `WorkflowCoordinator` stub named from `env.WORKFLOW_COORDINATOR.idFromName("primary")`
- Produces all routes in the approved design specification

- [ ] **Step 1: Write failing route/security tests**

```js
import { SELF } from "cloudflare:test";
import { describe, expect, it } from "vitest";

describe("protected Worker", () => {
  it("does not expose workflow assets or data before login", async () => {
    expect((await SELF.fetch("https://agent.test/")).status).toBe(200);
    expect((await SELF.fetch("https://agent.test/app")).status).toBe(401);
    expect((await SELF.fetch("https://agent.test/api/bootstrap")).status).toBe(401);
    expect((await SELF.fetch("https://agent.test/data/faculty.json")).status).toBe(404);
  });

  it("contains no email sending route", async () => {
    const response = await SELF.fetch("https://agent.test/api/send", { method: "POST" });
    expect(response.status).toBe(404);
  });
});
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `cd protected_phd_agent && pnpm test -- test/worker.test.js`

Expected: FAIL because protected routing is not implemented.

- [ ] **Step 3: Implement exact routing rules**

`src/worker.js` must:

1. Serve `/`, `/login.html`, `/login.js`, and the shared `/style.css` as the data-free login shell/assets.
2. Handle `POST /api/login` without a prior session.
3. Require `authenticate` for `/app`, `/index.html`, `/app.js`, `/logos/*`, and every other `/api/*` route.
4. Route bootstrap, update, export and one-time import through the singleton coordinator stub.
5. Require CSRF/origin guards for logout and authenticated updates. The one-time import route instead requires its bearer migration secret, the unset `migration_complete` marker, JSON content type, and a dedicated 10 MiB body limit because the CLI import has no browser session.
6. Return 404 for all unknown API routes and all `/data/*` paths.
7. Attach the approved security headers to assets and JSON responses.

- [ ] **Step 4: Verify GREEN and commit**

Run: `cd protected_phd_agent && pnpm test -- test/worker.test.js && pnpm run check`

Expected: route/security tests pass and the Worker dry-run succeeds.

```bash
git add protected_phd_agent/src/worker.js protected_phd_agent/test/worker.test.js protected_phd_agent/public/login.html protected_phd_agent/public/login.js protected_phd_agent/public/index.html
git commit -m "feat: gate PhD workflow routes"
```

---

### Task 5: Adapt the dossier UI for authenticated cloud synchronization

**Files:**
- Create: `protected_phd_agent/public/app.js`
- Create: `protected_phd_agent/public/style.css`
- Create: `protected_phd_agent/public/logos/*.svg`
- Create: `protected_phd_agent/test/static.test.js`

**Interfaces:**
- Consumes: `GET /api/session`, `POST /api/login`, `GET /api/bootstrap`, `PUT /api/artifacts/:id`, `PUT /api/faculty/:id`, `GET /api/export`, `POST /api/logout`
- Produces UI state: `{authenticated, csrf, revision, dirtyRecords, activeDossierId, syncState}`

- [ ] **Step 1: Write failing static contract tests**

```js
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";

describe("private dossier UI", () => {
  it("has login, sync, export and logout controls without send controls", async () => {
    const login = await readFile("public/login.html", "utf8");
    const html = await readFile("public/index.html", "utf8");
    const js = await readFile("public/app.js", "utf8");
    expect(login).toContain("id=\"workflow-password\"");
    expect(html).toContain("id=\"sync-cloud\"");
    expect(html).toContain("id=\"export-backup\"");
    expect(html).toContain("id=\"logout\"");
    expect(js).toContain("409");
    expect(js).toContain("unsynchronized");
    expect(`${login}\n${html}\n${js}`).not.toMatch(/send email|smtp|mailto:/i);
  });
});
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `cd protected_phd_agent && pnpm test -- test/static.test.js`

Expected: FAIL because the cloud-sync frontend is incomplete.

- [ ] **Step 3: Implement the authenticated UI**

Implement `login.js` so it posts the password to `/api/login`, clears the input immediately, retains no response data, and navigates to `/app` on success. Port the current dossier navigation, institution marks, research summaries, match memo, correction alert and editable email workbench into `app.js` without embedding production records. Implement these exact client behaviors:

```js
const state = {
  authenticated: false,
  csrf: "",
  revision: 0,
  faculty: [],
  artifacts: [],
  dirtyRecords: new Map(),
  activeDossierId: null,
  syncState: "clean"
};
```

Implement `login(password)`, `bootstrap()`, `markDirty(collection, id, patch)`, `syncCloud()`, `exportBackup()`, and `logout()` with the interfaces defined above. `login` sends the password only in the JSON request body and retains the returned CSRF token in memory. `bootstrap` replaces in-memory production arrays from the authenticated response. `markDirty` merges patches by `collection:id`. `syncCloud` sends patches sequentially with the latest returned revision. `exportBackup` downloads the authenticated response without caching. `logout` sends the CSRF header and zeroes all in-memory production state.

On HTTP 401, keep unsynchronized editor text in memory and show the login shell. On HTTP 409, do not clear `dirtyRecords`; offer export and refresh. Do not store production data, password, session cookie, or CSRF token in `localStorage`, `sessionStorage`, IndexedDB, or URL parameters.

- [ ] **Step 4: Verify GREEN, run browser-level local QA, and commit**

Create an ignored `.dev.vars` containing synthetic local-only values, confirm `git check-ignore .dev.vars` succeeds, then run: `cd protected_phd_agent && pnpm test -- test/static.test.js && pnpm test && pnpm run dev`

Expected: tests pass; a local browser can log in with the synthetic `.dev.vars` secret, navigate 28 synthetic local-test dossiers, edit, sync, refresh, export and log out; no console errors appear.

```bash
git add protected_phd_agent/public protected_phd_agent/test/static.test.js
git commit -m "feat: add private dossier cloud sync UI"
```

---

### Task 6: Build the private migration, backup and leak-check tools

**Files:**
- Create: `protected_phd_agent/scripts/prepare_private_migration.py`
- Create: `protected_phd_agent/scripts/verify_private_migration.py`
- Create: `protected_phd_agent/scripts/verify_rewritten_history.py`
- Create: `protected_phd_agent/__init__.py`
- Create: `protected_phd_agent/scripts/__init__.py`
- Create: `protected_phd_agent/test_py/__init__.py`
- Create: `protected_phd_agent/test_py/test_migration.py`
- Create: `docs/private-phd-agent-operations.md`
- Modify: `.gitignore`
- Modify: `_config.yml`

**Interfaces:**
- Produces: `prepare(source_root, private_root) -> manifest dict`
- Produces ignored files: `phd_application_agent/private_data/cloudflare-seed.json`, `manifest.json`, `local-app-snapshot/`
- Produces: `verify_seed(seed_path, manifest_path) -> None`
- Produces: `verify_history(repo_root, manifest_path) -> None`

- [ ] **Step 1: Write failing migration tests**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from protected_phd_agent.scripts.prepare_private_migration import prepare
from protected_phd_agent.scripts.verify_private_migration import verify_seed


class MigrationTests(unittest.TestCase):
    def test_prepare_copies_records_and_emits_hash_manifest_without_plaintext_terms(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            private = root / "private"
            (source / "data").mkdir(parents=True)
            (source / "data" / "faculty.json").write_text('[{"id":"fac_1","name":"Synthetic Advisor"}]')
            (source / "data" / "artifacts.json").write_text('[{"id":"art_1","content":"Synthetic draft"}]')
            manifest = prepare(source, private)
            self.assertEqual(1, manifest["counts"]["faculty"])
            self.assertNotIn("Synthetic Advisor", json.dumps(manifest))
            verify_seed(private / "cloudflare-seed.json", private / "manifest.json")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `python3 -m unittest protected_phd_agent.test_py.test_migration -v`

Expected: FAIL because migration modules do not exist.

- [ ] **Step 3: Implement safe migration tooling**

`prepare` reads the existing local JSON collections, copies the current local application into `local-app-snapshot/`, writes a schema-versioned coordinator seed, and records SHA-256 hashes and counts. It records only HMAC-SHA-256 leak probes generated with a random local manifest key; it never writes names, email excerpts, or the password into the manifest.

`verify_seed` recomputes counts/hashes. `verify_rewritten_history` enumerates reachable Git objects and fails on either removed paths or exact private probe matches while printing only object IDs/counts, never matched private text.

- [ ] **Step 4: Add permanent recommit/build exclusions**

Append these exact root `.gitignore` rules:

```gitignore
/phd_application_agent/
/phd-advisor-summary/
**/private_data/
```

Add `phd_application_agent`, `phd-advisor-summary`, `protected_phd_agent`, and every `private_data` path to `_config.yml` `exclude` so local private files and Worker source cannot enter `_site`; the homepage links to the separate Worker origin.

Create `docs/private-phd-agent-operations.md` with exact commands for `wrangler secret put`, password/session secret rotation, authenticated JSON export, one-time restore into an empty coordinator, Worker version rollback, logout/session invalidation, the external bundle/private-backup locations, and required fresh-clone instructions after rewritten history. The runbook names secret variables but contains no values or production records.

- [ ] **Step 5: Verify GREEN and create the recoverable backups**

Run:

```bash
python3 -m unittest protected_phd_agent.test_py.test_migration -v
python3 protected_phd_agent/scripts/prepare_private_migration.py --source phd_application_agent --private phd_application_agent/private_data
python3 protected_phd_agent/scripts/verify_private_migration.py --seed phd_application_agent/private_data/cloudflare-seed.json --manifest phd_application_agent/private_data/manifest.json
ditto phd_application_agent/private_data ../ShuoLv-fp.github.io-private-agent-backup
git bundle create ../ShuoLv-fp.github.io-before-private-agent.bundle --all
git bundle verify ../ShuoLv-fp.github.io-before-private-agent.bundle
```

Expected: tests pass; seed verification reports the expected record counts without printing records; the external private-data copy contains the same manifest hash; Git reports the external bundle as valid.

- [ ] **Step 6: Retire tracked local workflow edits only after both backups verify**

Run `git restore --source=HEAD -- phd_application_agent phd-advisor-summary` after verifying both the in-repository ignored backup and the external copy. This discards only the tracked working copies now preserved in `local-app-snapshot/`; it does not remove ignored private data. Confirm `git status --short` has no remaining changes under either old workflow path.

- [ ] **Step 7: Commit only data-free tooling, runbook and exclusions**

```bash
git add .gitignore _config.yml protected_phd_agent/__init__.py protected_phd_agent/scripts protected_phd_agent/test_py docs/private-phd-agent-operations.md
git status --short
git commit -m "feat: add private workflow migration safeguards"
```

Expected: `phd_application_agent/private_data/` does not appear in staged or committed files.

---

### Task 7: Add and verify the homepage Lean-icon entry

**Files:**
- Create: `tests/test_phd_agent_entry.py`
- Modify: `_config.yml`
- Modify: `_pages/includes/technical_skills.md`
- Modify: `_pages/includes/zh/technical_skills.md`

**Interfaces:**
- Consumes: `_config.yml` key `phd_agent_url`
- Produces: only the Lean image anchor uses `{{ site.phd_agent_url }}`

- [ ] **Step 1: Write the failing Jekyll entry test**

```python
from pathlib import Path
import unittest


class PhdAgentEntryTests(unittest.TestCase):
    def test_both_lean_images_use_one_configured_protected_url(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        self.assertIn("phd_agent_url:", config)
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn('href="{{ site.phd_agent_url }}"', text)
            self.assertIn("[Lean](https://lean-lang.org/)", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `python3 -m unittest tests.test_phd_agent_entry -v`

Expected: FAIL because `phd_agent_url` and the image anchors do not exist.

- [ ] **Step 3: Deploy the empty-state Worker once and add the observed URL**

Run `cd protected_phd_agent && pnpm exec wrangler login && pnpm run check && pnpm exec wrangler deploy`. At this point no production data has been imported and no workflow password is configured, so only the data-free login shell can render and login cannot succeed. Write the exact `workers.dev` URL printed by Wrangler to `_config.yml` as `phd_agent_url`. Wrap each Lean `<img>` in:

```html
<a href="{{ site.phd_agent_url }}" aria-label="Open private PhD application workflow" rel="nofollow">
  <img src="/_pages/includes/images/Lean.svg" style="width: auto; height: 20px; vertical-align: middle; margin: 0 4px;">
</a>
```

Do not wrap or change the adjacent `[Lean](https://lean-lang.org/)` text link.

- [ ] **Step 4: Verify Jekyll output and commit**

Run: `python3 -m unittest tests.test_phd_agent_entry -v && bundle exec jekyll build`

Expected: test and build pass; rendered English and Chinese pages contain the protected image URL and retain the Lean official text URL.

```bash
git add _config.yml _pages/includes/technical_skills.md _pages/includes/zh/technical_skills.md tests/test_phd_agent_entry.py
git commit -m "feat: link Lean icon to private PhD agent"
```

---

### Task 8: Deploy Cloudflare resources and import production data

**Files:**
- Modify: `protected_phd_agent/wrangler.jsonc` only if Wrangler writes automatically provisioned IDs
- Modify locally/ignored: `protected_phd_agent/.dev.vars` only when rotating synthetic local values

**Interfaces:**
- Consumes: validated `cloudflare-seed.json`, four interactive secrets, Wrangler login
- Produces: deployed Worker URL, populated coordinator state, KV recovery snapshot

- [ ] **Step 1: Run the full pre-deployment suite**

Run: `cd protected_phd_agent && pnpm test && pnpm run check && cd .. && python3 -m unittest discover -s tests -v`

Expected: all Worker, migration and homepage tests pass; Worker dry-run and Jekyll-related tests exit 0.

- [ ] **Step 2: Confirm the Cloudflare session with user presence if it expired**

Run: `cd protected_phd_agent && pnpm exec wrangler whoami`

Expected: Wrangler prints the authenticated account without exposing credentials. If it reports no session, run `pnpm exec wrangler login`; the user completes authorization directly and reruns `whoami`.

- [ ] **Step 3: Set secrets interactively without writing them to disk**

In one interactive terminal session, use hidden shell input for the user-selected password and random generated values for the other secrets:

```bash
read -s "PHD_WORKFLOW_PASSWORD?Workflow password: "
printf '%s' "$PHD_WORKFLOW_PASSWORD" | pnpm exec wrangler secret put WORKFLOW_PASSWORD
unset PHD_WORKFLOW_PASSWORD
openssl rand -hex 32 | pnpm exec wrangler secret put SESSION_SECRET
openssl rand -hex 32 | pnpm exec wrangler secret put RATE_LIMIT_SECRET
read -s "PHD_MIGRATION_SECRET?One-time migration secret: "
export PHD_MIGRATION_SECRET
printf '%s' "$PHD_MIGRATION_SECRET" | pnpm exec wrangler secret put MIGRATION_SECRET
```

Expected: Wrangler confirms each secret name without printing its value. Keep only `PHD_MIGRATION_SECRET` in the current shell until Step 5, then unset it.

- [ ] **Step 4: Deploy with automatic KV provisioning**

Run: `pnpm exec wrangler deploy`

Expected: Wrangler deploys `shuo-phd-agent`, provisions `PHD_AGENT_DATA` because its configuration omits an ID, applies Durable Object migration `v1`, and prints the Worker URL. Confirm it matches the URL recorded in Task 7, then export `PHD_AGENT_URL` with exactly that observed URL for Step 5.

- [ ] **Step 5: Import once and verify authenticated readback**

Run from the same secret-bearing terminal session:

```bash
curl --fail-with-body --request POST "$PHD_AGENT_URL/api/admin/import" \
  --header "Authorization: Bearer $PHD_MIGRATION_SECRET" \
  --header "Content-Type: application/json" \
  --data-binary @../phd_application_agent/private_data/cloudflare-seed.json
unset PHD_MIGRATION_SECRET
python3 scripts/verify_private_migration.py \
  --seed ../phd_application_agent/private_data/cloudflare-seed.json \
  --manifest ../phd_application_agent/private_data/manifest.json \
  --remote "$PHD_AGENT_URL"
```

Expected: import returns revision `1`; a second import attempt returns 409; remote verification confirms the same schema version, record counts and selected hashes without printing production records.

- [ ] **Step 6: Redeploy and commit any non-secret auto-provisioned IDs**

Run: `pnpm exec wrangler deploy && git diff --check`

Expected: protected URL responds with the login shell; unauthenticated bootstrap is 401; any Wrangler-written KV namespace ID may be committed because Cloudflare documents namespace IDs as public.

```bash
git add protected_phd_agent/wrangler.jsonc
git commit -m "chore: record Cloudflare resource bindings"
```

Skip the commit when Wrangler made no configuration change.

---

### Task 9: Rewrite public Git history and publish the safe repository

**Files:**
- Removes from all reachable history: `phd_application_agent/`, `phd-advisor-summary/`
- Preserves current safe paths: `protected_phd_agent/`, homepage sources, specs/plans, runbook

**Interfaces:**
- Consumes: valid external Git bundle, verified private seed/manifest, verified Cloudflare deployment, clean working tree, recorded remote head
- Produces: rewritten local refs and force-updated GitHub refs without old workflow paths

- [ ] **Step 1: Verify destructive-operation prerequisites**

Run:

```bash
git fetch origin --prune --tags
export RECORDED_REMOTE_MAIN=$(git rev-parse origin/main)
printf '%s\n' "$RECORDED_REMOTE_MAIN"
git status --short
git bundle verify ../ShuoLv-fp.github.io-before-private-agent.bundle
python3 protected_phd_agent/scripts/verify_private_migration.py \
  --seed phd_application_agent/private_data/cloudflare-seed.json \
  --manifest phd_application_agent/private_data/manifest.json \
  --remote "$PHD_AGENT_URL"
```

Expected: remote head is recorded; working tree has no tracked changes; bundle and remote migration verification pass. Stop immediately if any check fails.

- [ ] **Step 2: Confirm tool version and affected refs**

Run: `git filter-repo --version && git for-each-ref --format='%(refname)' refs/heads refs/tags`

Expected: `git-filter-repo` is at least 2.47 and the ref list is understood before rewriting.

- [ ] **Step 3: Rewrite all local refs**

Run:

```bash
git filter-repo --force --sensitive-data-removal --invert-paths \
  --path phd_application_agent \
  --path phd-advisor-summary
```

Expected: filter-repo reports changed refs and first changed commits; the safe `protected_phd_agent/` directory and design/plan remain reachable.

- [ ] **Step 4: Verify rewritten history before any push**

Run:

```bash
python3 protected_phd_agent/scripts/verify_rewritten_history.py \
  --repo . \
  --manifest ../ShuoLv-fp.github.io-private-agent-backup/manifest.json
git log --all -- phd_application_agent phd-advisor-summary
git status --short
```

Expected: verifier exits 0, path log is empty, and no sensitive matched text is printed. If it fails, do not push; restore or inspect using the external bundle.

- [ ] **Step 5: Re-add the remote and verify lease target**

`git-filter-repo` may remove `origin`. Re-add `https://github.com/ShuoLv-fp/ShuoLv-fp.github.io.git`, fetch it, and confirm that its current `main` still equals the remote head recorded in Step 1. Stop if it differs.

- [ ] **Step 6: Force-update the approved refs**

Run:

```bash
git push --force-with-lease=main:$RECORDED_REMOTE_MAIN origin main
git push --force-with-lease origin --tags
```

Expected: GitHub accepts rewritten `main` and affected tags. If branch protection blocks the push, pause for the user to temporarily allow force pushes; do not bypass repository protection through another route.

- [ ] **Step 7: Verify remote refs and repository content**

Run a fresh temporary clone, execute the history verifier against it, build Jekyll, and run the safe Worker tests. Confirm the public repository no longer exposes the removed paths in reachable history.

---

### Task 10: End-to-end production verification

**Files:**
- Modify only if verification finds a tested defect: corresponding `protected_phd_agent` source and test

**Interfaces:**
- Consumes: live GitHub Pages homepage and live Cloudflare Worker
- Produces: evidence that the approved acceptance criteria hold

- [ ] **Step 1: Verify unauthenticated protection**

Check the live Worker root, `/app`, `/api/bootstrap`, `/api/export`, `/data/faculty.json`, and a logo asset. Before authentication, only the login shell is 200; all workflow/data routes are 401 or 404 and disclose no record content.

- [ ] **Step 2: Verify authentication and lockout**

Use a disposable test client identity for five wrong attempts and confirm HTTP 429 without locking the user's normal browser session. Then use the correct password in the normal session and confirm the 12-hour secure cookie attributes.

- [ ] **Step 3: Verify sync, revision conflict, refresh and export**

Edit one outreach subject with a reversible marker, sync it, refresh, and confirm persistence. Restore the original subject and sync again. Open a second authenticated session from the older revision and confirm its save receives HTTP 409 without overwriting. Export the backup and compare revision/counts to the private manifest.

- [ ] **Step 4: Verify the hidden homepage entry**

On both live English and Chinese homepage variants, click the Lean image and confirm navigation to the protected Worker. Confirm the Lean text still opens the official Lean site.

- [ ] **Step 5: Run fresh complete verification**

Run:

```bash
python3 -m unittest discover -s tests -v
cd protected_phd_agent
pnpm test
pnpm run check
cd ..
bundle exec jekyll build
python3 protected_phd_agent/scripts/verify_rewritten_history.py \
  --repo . \
  --manifest ../ShuoLv-fp.github.io-private-agent-backup/manifest.json
```

Expected: every command exits 0; no secret value or private record is printed.

- [ ] **Step 6: Report publication evidence**

Report the live homepage URL, protected Worker URL, test counts, migration record counts, rewritten-ref verification, GitHub Pages deployment state, local bundle path, and private backup path. Do not report the password, secret values, private record excerpts, or session cookies.
