# PhD Agent Private Repository Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the complete PhD Agent source and its current Research Proposal work into `ShuoLv-fp/ShuoLv-agent-private`, then remove `protected_phd_agent` from the public homepage repository without changing private Cloudflare runtime data.

**Architecture:** Use `git subtree split` to turn the committed `protected_phd_agent` history into a standalone repository, then overlay the current uncommitted working tree into that private checkout. Verify the destination locally and on GitHub before recording a normal deletion commit in the public repository. Real proposal content remains exclusively in the existing private Cloudflare Durable Object/KV; neither Git repository stores it.

**Tech Stack:** Git subtree history, GitHub private repositories, Cloudflare Workers/Durable Objects/KV, Wrangler 4, Vitest, Python unittest.

## Global Constraints

- The GitHub repository name is exactly `ShuoLv-agent-private` under account `ShuoLv-fp`.
- The destination repository must be verified as private before the first push.
- Preserve the committed history of `protected_phd_agent` and all current uncommitted Proposal feature work.
- Do not commit proposal prose, Chinese review notes, advisor evidence, online snapshots, credentials, migration batches, `.dev.vars`, `.wrangler`, `node_modules`, `public/research`, or `private_data`.
- Keep `snapshot:latest` and `proposal-generation:checkpoint` in the existing private Cloudflare KV namespace; do not overwrite production state during repository migration.
- Do not rewrite or force-push public Git history.
- Do not remove the public directory until the private checkout and remote have both been verified.
- Work directly with the existing `main` branch as explicitly approved by the user.

---

### Task 1: Build the standalone private candidate with preserved history

**Files:**
- Source: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/**`
- Create: `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private/**`
- Create: `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private/.gitignore`

**Interfaces:**
- Consumes: the committed public repository history plus its current `protected_phd_agent` working tree.
- Produces: a standalone local Git repository whose root is the former `protected_phd_agent` directory.

- [ ] **Step 1: Capture a read-only safety inventory**

Run from `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io`:

```bash
git status --short
git log -1 --oneline
git remote -v
git ls-files protected_phd_agent
```

Expected: `main` contains the approved migration-design commit; all application changes are confined to `protected_phd_agent` plus the known root `.gitignore` edit.

- [ ] **Step 2: Split the committed application history**

```bash
git subtree split --prefix=protected_phd_agent -b codex/private-agent-history
```

Expected: Git creates `codex/private-agent-history` and prints its commit ID without changing the public working tree.

- [ ] **Step 3: Clone the split history into the destination path**

```bash
git clone --branch codex/private-agent-history --single-branch /Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io /Users/shuolv/Documents/GitHub/ShuoLv-agent-private
```

Expected: the destination exists as a standalone repository and files such as `package.json`, `src/worker.js`, and `wrangler.jsonc` are at its root.

- [ ] **Step 4: Overlay current tracked and untracked application work**

```bash
rsync -a --exclude=.git --exclude=node_modules --exclude=.wrangler --exclude=.dev.vars --exclude=__pycache__ --exclude=public/research /Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/ /Users/shuolv/Documents/GitHub/ShuoLv-agent-private/
```

Expected: Proposal implementation and tests appear as modifications/untracked files only in the private candidate; no private runtime data is copied.

- [ ] **Step 5: Add the private repository ignore policy**

Create `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private/.gitignore` with exactly:

```gitignore
.dev.vars
.env
.env.*
.wrangler/
node_modules/
public/research/
private_data/
**/__pycache__/
**/*.pyc
*proposal*batch*.json
*proposal*checkpoint*.json
*snapshot*.json
*evidence*.json
*migration-secret*
*workflow-password*
```

- [ ] **Step 6: Verify the candidate contains no forbidden tracked or staged data**

```bash
git status --short
git ls-files
git diff --check
```

Expected: only source code, configuration, documentation, and synthetic tests are candidates for commit; no path matching the private-data rules is tracked.

- [ ] **Step 7: Commit the current Proposal feature in the private repository**

```bash
git add .gitignore OPERATIONS.md public/app.js public/style.css scripts/append_proposal_batch.py scripts/generate_proposal_batch.py scripts/validate_proposal_batch.mjs src/coordinator.js src/proposal-append.js src/worker.js test/static.test.js test/proposal-append.test.js test/proposal-coordinator.test.js test/proposal-worker.test.js test_py/test_proposal_batch_tools.py test_py/test_proposal_generation.py
git commit -m "feat: add private tailored research proposals"
```

Expected: the private candidate is clean except for ignored runtime/dependency directories added during later verification.

### Task 2: Create and push the GitHub private repository

**Files:**
- Modify: `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private/.git/config`

**Interfaces:**
- Consumes: the verified local standalone repository from Task 1.
- Produces: private GitHub repository `https://github.com/ShuoLv-fp/ShuoLv-agent-private` with default branch `main`.

- [ ] **Step 1: Create the destination through the authenticated GitHub UI**

Open `https://github.com/new` in the user's authenticated browser, set owner `ShuoLv-fp`, repository name `ShuoLv-agent-private`, visibility `Private`, and leave README, `.gitignore`, and license initialization disabled.

Expected: GitHub shows the new repository with a `Private` badge and an empty-repository setup page.

- [ ] **Step 2: Rename the local branch and attach the verified private remote**

```bash
git branch -M main
git remote remove origin
git remote add origin https://github.com/ShuoLv-fp/ShuoLv-agent-private.git
git remote -v
```

Expected: both fetch and push URLs target only `ShuoLv-fp/ShuoLv-agent-private.git`.

- [ ] **Step 3: Push the standalone history**

```bash
git push -u origin main
```

Expected: push succeeds without force and establishes `origin/main`.

- [ ] **Step 4: Verify remote privacy and repository contents**

Refresh the GitHub page and confirm the `Private` badge, default branch `main`, Proposal source files, and preserved application commit history. Confirm no private proposal JSON, evidence, snapshot, or credential file appears in the file tree.

### Task 3: Restore ignored local dependencies and verify the private checkout

**Files:**
- Move locally, never track: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/node_modules/`
- Move locally, never track: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/public/research/`
- Move locally if present, never track: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/.wrangler/`

**Interfaces:**
- Consumes: ignored local dependencies/private briefing assets and the pushed private checkout.
- Produces: a locally runnable private checkout with no ignored assets left under the public repository path.

- [ ] **Step 1: Move ignored runtime directories into the private checkout**

Move each existing directory to the matching private path, preserving permissions. Do not copy or print contents. If a destination directory already exists, stop and compare paths before merging.

Expected: `node_modules`, `public/research`, and `.wrangler` exist only under `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private` and remain ignored by Git.

- [ ] **Step 2: Run the JavaScript/Worker test suite**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vitest/vitest.mjs run
```

Expected: all Vitest files and tests pass.

- [ ] **Step 3: Run the Python batch-tool test suite**

```bash
env PATH="/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/usr/bin:/bin:/usr/sbin:/sbin" /Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s test_py -v
```

Expected: all Python tests pass.

- [ ] **Step 4: Verify private briefings and deployment configuration**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node scripts/verify-private-briefings.mjs
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/wrangler/bin/wrangler.js deploy --dry-run
git diff --check
git status --short --ignored
```

Expected: briefing validation and Wrangler dry-run pass; the Git working tree is clean and all private/dependency paths are ignored.

- [ ] **Step 5: Verify Cloudflare state without printing private content**

```bash
/Users/shuolv/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/wrangler/bin/wrangler.js kv key list --binding PHD_AGENT_DATA --remote --prefix proposal-generation:
```

Expected: the private `proposal-generation:checkpoint` key exists; no key value is printed and no state is changed.

### Task 4: Remove the application from the public homepage repository

**Files:**
- Delete: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent/**`
- Modify: `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/.gitignore`

**Interfaces:**
- Consumes: successful private remote and private-checkout verification from Tasks 2–3.
- Produces: a public `main` tree with no `protected_phd_agent` directory.

- [ ] **Step 1: Record tracked deletion only after private verification**

```bash
git rm -r protected_phd_agent
```

Expected: all previously tracked application paths are staged for deletion. Untracked Proposal implementation files may remain temporarily and must be handled in Step 2.

- [ ] **Step 2: Move any remaining public-path residue to a recoverable quarantine**

Move the remaining `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/protected_phd_agent` directory, if it still exists, to `/Users/shuolv/.Trash/protected_phd_agent-public-residue-2026-09-08`. Refuse to overwrite an existing quarantine target.

Expected: no `protected_phd_agent` directory remains in the public working tree.

- [ ] **Step 3: Remove application-only public ignore rules**

Edit the public `.gitignore` to remove:

```gitignore
protected_phd_agent/.dev.vars
protected_phd_agent/.wrangler/
protected_phd_agent/node_modules/
protected_phd_agent/public/research/
**/private_data/
```

Keep unrelated homepage rules and the general Python cache rules unchanged.

- [ ] **Step 4: Verify the public deletion scope**

```bash
git status --short
git diff --cached --stat
git diff --cached --name-only
git diff --check
test ! -e protected_phd_agent
```

Expected: the staged change deletes only the application, `.gitignore` has only the documented cleanup, and unrelated homepage files are untouched.

- [ ] **Step 5: Commit and push the public removal**

```bash
git add .gitignore
git commit -m "chore: move phd agent to private repository"
git push origin main
```

Expected: public `origin/main` contains the migration design/plan and the normal deletion commit, with no force-push.

- [ ] **Step 6: Remove the temporary local subtree branch**

```bash
git branch -D codex/private-agent-history
```

Expected: only normal public branches remain; the private repository has its independent history.

### Task 5: Redirect the continuation workflow and perform final verification

**Files:**
- Update: Codex heartbeat `resume-private-proposals`

**Interfaces:**
- Consumes: private checkout path and existing private Cloudflare checkpoint.
- Produces: continued Proposal generation from the private repository only.

- [ ] **Step 1: Update the heartbeat repository path**

Change `resume-private-proposals` so every code command runs from `/Users/shuolv/Documents/GitHub/ShuoLv-agent-private`. Preserve its daily schedule, quota-aware stopping, Cloudflare KV checkpointing, aggregate-only reporting, and local temporary-file cleanup rules.

Expected: the automation no longer references the public homepage repository for Agent code.

- [ ] **Step 2: Re-check both repositories**

```bash
git -C /Users/shuolv/Documents/GitHub/ShuoLv-agent-private status --short
git -C /Users/shuolv/Documents/GitHub/ShuoLv-agent-private log -3 --oneline
git -C /Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io status --short
git -C /Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io log -3 --oneline
```

Expected: both repositories are clean; private history ends with the Proposal feature commit and public history ends with the removal commit.

- [ ] **Step 3: Confirm no private local working files remain outside the private checkout**

Check only filenames and permissions, never contents. Confirm no proposal batch, evidence, snapshot, or credential working file exists under the public repository or `/tmp`; ignored runtime assets may exist only inside the private checkout.

Expected: private content persists only in Cloudflare storage, and neither Git index tracks it.

- [ ] **Step 4: Report migration outcome**

Report the private repository URL, both final commit IDs, verification counts, Cloudflare checkpoint presence, automation status, and the explicit fact that public history was not rewritten. Do not report private content, source URLs, secrets, or advisor identifiers.
