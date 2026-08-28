# Password-Protected PhD Application Agent: Design Specification

**Date:** 2026-08-29  
**Status:** Approved in conversation; awaiting written-spec review  
**Repository:** `ShuoLv-fp/ShuoLv-fp.github.io`

## 1. Objective

Publish the PhD Application Agent as a password-protected Cloudflare application while keeping the academic homepage on GitHub Pages. Clicking the Lean icon on either the English or Chinese homepage opens the protected workflow. Advisor dossiers, profile-fit analysis, application state, and outreach drafts must not remain as plaintext in the public Git repository or its normal Git history.

The workflow remains draft-only. It can edit, copy, export, and synchronize outreach drafts, but it must not send email.

## 2. Constraints and Security Boundary

- `https://shuolv-fp.github.io/` remains the public Jekyll homepage.
- The protected workflow is deployed to a dedicated Cloudflare Pages/Workers address. Its final URL is written to the Jekyll configuration only after Cloudflare creates the project.
- GitHub Pages cannot provide real password protection for one subpath, so the workflow must not be hosted directly under the `github.io` origin.
- The user-selected workflow password is stored only as a Cloudflare secret. Its plaintext value must not appear in Git, HTML, JavaScript, cookies, logs, fixtures, screenshots, or generated build output.
- The six-digit password is supplemented by server-side rate limiting. Five failed attempts from the same rate-limit identity within 15 minutes block further attempts for 15 minutes.
- Sensitive production data lives in Cloudflare KV and in a local ignored backup. The public repository contains only program code and synthetic test fixtures.
- Existing public Git history containing workflow data is rewritten after a recoverable local backup is created and after the Cloudflare migration is verified.
- History rewriting removes the data from the repository's ordinary refs and interface, but cannot erase independent clones, forks, screenshots, or caches held by third parties.

## 3. User Experience

### 3.1 Hidden homepage entry

The Lean image in both `_pages/includes/technical_skills.md` and `_pages/includes/zh/technical_skills.md` becomes the discreet entry to the protected workflow. Only the image links to the Cloudflare application. The adjacent `Lean` text continues linking to `https://lean-lang.org/`.

The external workflow URL is stored once in `_config.yml` and referenced by both language variants, avoiding duplicated deployment URLs.

### 3.2 Login

An unauthenticated visitor receives only the login shell. No workflow HTML containing private content and no production JSON are returned before authentication.

The user enters the shared password. A successful login creates a signed session cookie with these properties:

- `HttpOnly`
- `Secure`
- `SameSite=Strict`
- twelve-hour expiry
- a random session identifier signed with an independent `SESSION_SECRET`

The login response also establishes a CSRF token for authenticated mutations. The UI provides an explicit logout action that invalidates the current session.

### 3.3 Dossier workflow

After login, the existing Advisor Dossiers interface loads from the authenticated bootstrap API. The 28 curated advisor/lab/programme entries preserve their source order, research summaries, profile-fit analysis, cautions, corrected-source audit notes, institution marks, and tailored outreach drafts.

Editing occurs in browser memory first. The page clearly distinguishes:

- last synchronized version;
- unsynchronized local changes;
- synchronization in progress;
- saved version and timestamp;
- conflict or validation failure.

The main persistence action is labelled **Sync cloud**. It writes only changed, allowlisted fields to Cloudflare KV. It does not use a GitHub personal access token and does not create a Git commit for content edits.

## 4. Architecture

### 4.1 Public GitHub repository

The repository retains:

- the Jekyll homepage and its Lean-icon link;
- the data-free PhD Agent frontend;
- Cloudflare Pages Functions/Worker code;
- static local institution marks;
- schema definitions and synthetic fixtures;
- automated tests and deployment documentation.

The repository does not retain:

- production faculty/advisor JSON;
- profile-fit analysis data;
- outreach email bodies or subjects;
- application tracking state;
- the fixed password or session secrets;
- source constants that reconstruct the production dossier records.

### 4.2 Cloudflare application

The Cloudflare project serves the login shell, authenticated application assets, and same-origin APIs. Middleware protects all workflow and data routes. The minimum endpoint surface is:

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/login` | Verify password, apply rate limit, issue session and CSRF state |
| `POST` | `/api/logout` | Invalidate the current session |
| `GET` | `/api/session` | Return authenticated state without exposing secrets |
| `GET` | `/api/bootstrap` | Return the current versioned workflow data |
| `PUT` | `/api/faculty/:id` | Update allowlisted dossier fields |
| `PUT` | `/api/artifacts/:id` | Update allowlisted draft fields |
| `GET` | `/api/export` | Download an authenticated JSON backup |

No send-mail, SMTP, webhook, arbitrary proxy, or generic file-write endpoint is permitted.

### 4.3 Durable Object and Cloudflare KV model

Workers KV is eventually consistent and cannot provide an atomic compare-and-swap operation. A single Durable Object named `WorkflowCoordinator` therefore owns the authoritative workflow state and serializes all reads and mutations. Its storage contains faculty, artifacts, profile, applications, programmes, activity metadata, active session records, schema version, and global revision. Each mutation includes the revision observed by the browser.

After each accepted mutation, the coordinator writes a versioned recovery snapshot to KV. KV is used for authenticated exports, migration verification, and disaster recovery, not for concurrency control. This preserves a private KV backup while ensuring the browser receives strongly ordered revisions from the Durable Object.

The coordinator rejects a mutation when the submitted revision is stale and returns a conflict response containing only the new revision identifier. The browser preserves the unsynchronized text and offers export before reload; it never silently overwrites the newer cloud state.

Writes validate:

- authenticated session;
- same-origin `Origin` header;
- CSRF token;
- known collection and record identifier;
- explicit field allowlist;
- expected data types;
- request and field size limits;
- current revision.

### 4.4 Local private backup

Before migration, production data is copied into `phd_application_agent/private_data/`. This directory is ignored by Git and explicitly excluded from the Jekyll build. A manifest records file hashes, record counts, schema version, and backup time.

The private backup remains usable by the local Python Agent and provides the source for one-time KV import. Exported cloud backups are also stored there when generated locally.

## 5. Authentication and Abuse Controls

The server compares the submitted password against a Cloudflare secret without logging either value. Authentication errors use a uniform response so callers cannot distinguish missing account state from a wrong password.

Rate-limit counters are stored in a dedicated KV keyspace with expiry. The key uses a server-secret HMAC of Cloudflare's client-address signal so the raw address is not persisted. Five failures in the 15-minute window trigger a 15-minute lock. Successful login clears the corresponding failure counter.

Session cookies contain no production data or password. They carry a random identifier, issue/expiry times, and an HMAC signature. An active-session record in KV permits immediate logout and revocation. The server verifies the signature, expiry, and active-session record for every protected request. Mutation requests additionally require a CSRF token tied to the session and an allowed origin.

Security headers include a restrictive Content Security Policy, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and denial of framing. Third-party scripts are not loaded on the protected workflow.

## 6. Data Migration and History Rewrite

Migration follows a fail-closed sequence:

1. Fetch the remote repository and confirm the expected branch head.
2. Create a full local Git bundle outside the working repository.
3. Copy production workflow data to `private_data/` and generate the manifest.
4. Create Cloudflare resources, secrets, Durable Object migration, and KV bindings.
5. Import production JSON into the coordinator and mirror its first recovery snapshot to KV without routing it through public build artifacts.
6. Verify record counts, stable identifiers, selected content hashes, and authenticated retrieval.
7. Build and test the data-free public application.
8. Rewrite all local Git refs to remove historical `phd_application_agent/` and `phd-advisor-summary/` content.
9. Re-add only the reviewed data-free application and homepage entry.
10. Search the rewritten refs and working tree for advisor names, draft excerpts, private JSON keys, and the plaintext password.
11. Push rewritten `main` and affected tags with lease protection after rechecking the remote head.
12. Confirm the new GitHub Pages build and protected Cloudflare deployment.

If Cloudflare import, authentication, or validation fails, history rewriting does not begin. If verification after rewriting fails, the local Git bundle and `private_data/` backup are retained for recovery.

## 7. Error Handling and Recovery

- **Wrong password:** show a generic error and remaining delay without echoing the password.
- **Rate limit:** return HTTP 429 and the retry time.
- **Expired session:** return HTTP 401; preserve unsynchronized browser text and prompt for login.
- **CSRF/origin failure:** return HTTP 403 and make no write.
- **Validation failure:** identify the invalid field without returning unrelated records.
- **Version conflict:** return HTTP 409; preserve the local draft and offer JSON export before refresh.
- **KV failure:** keep the page in unsynchronized state and allow retry or export.
- **Deployment failure:** keep the current public homepage link unchanged until the protected URL passes validation.
- **History rewrite problem:** stop before force-push and restore or inspect using the local Git bundle.

## 8. Testing and Acceptance Criteria

Automated tests cover:

- password and session secrets absent from repository and build output;
- protected routes reject unauthenticated requests;
- correct password creates a valid session;
- five failures trigger temporary lockout;
- invalid, expired, or modified cookies fail closed;
- mutations require valid CSRF and origin;
- field and collection allowlists reject unintended writes;
- stale revisions return a conflict without modifying KV;
- successful draft updates survive a new authenticated bootstrap request;
- export requires authentication and matches the current revision;
- the public application has no email-send capability;
- English and Chinese Lean images use the configured protected URL;
- the Lean text still links to the official Lean site;
- Jekyll and Cloudflare builds contain no production JSON.

Before release, browser checks verify login, lockout messaging, dossier navigation, institution marks, email editing, cloud synchronization, refresh persistence, conflict recovery, export, logout, and responsive layout.

Release is accepted only when:

1. an unauthenticated request cannot retrieve workflow data;
2. the password is absent from Git and built assets;
3. the authenticated workflow contains all migrated records;
4. a synchronized edit persists in KV;
5. rewritten repository refs no longer contain the removed workflow paths or sampled private strings;
6. both homepage language variants reach the protected Cloudflare URL through the Lean icon;
7. no email-sending endpoint exists;
8. the local backup and Git bundle are readable and retained.

## 9. Deployment Inputs Requiring User Presence

The implementation may require the user to authenticate to Cloudflare in the browser or CLI and approve access to the GitHub repository. The user never supplies Cloudflare or GitHub passwords in chat. Cloudflare secrets are entered through the provider's secret-management flow, not committed to disk.

The final Cloudflare project URL is discovered during deployment and then written into `_config.yml`. Until that URL is live and verified, the production homepage retains its existing Lean icon behavior.
