# PhD Agent Private Repository Migration Design

## Goal

Move the complete `protected_phd_agent` application out of the public homepage repository
and into a new GitHub private repository named `ShuoLv-agent-private`. Preserve the
application's relevant Git history and all current uncommitted Research Proposal feature
work. Remove the application directory from the current public branch only after the
private destination has been verified.

## Privacy boundary

The private Git repository will contain application source code, synthetic test fixtures,
deployment configuration, and operational tooling. It will not contain real proposal
prose, Chinese strategy notes, advisor evidence packages, authenticated exports,
credentials, or migration batches.

Those data remain exclusively in private Cloudflare storage:

- Durable Object storage is the authoritative runtime workflow store.
- `snapshot:latest` in the existing private KV namespace remains the recovery snapshot.
- `proposal-generation:checkpoint` in the same namespace remains the resumable private
  generation checkpoint.
- Temporary local copies must use mode `0600`, stay outside every Git repository, and be
  deleted after each verified Cloudflare upload.

No R2 dependency will be introduced because R2 is not enabled for the account and enabling
a potentially billable product is outside this migration.

## Repository migration

The migration will preserve the committed history for `protected_phd_agent` with a Git
subtree split. The split branch becomes the history of the new private repository, with
the former subdirectory contents located at its root. Current uncommitted changes are then
copied onto that private working tree and committed there, never committed to the public
repository.

The private repository will add a root `.gitignore` covering at minimum:

- `.dev.vars` and other local secret files
- `.wrangler/` and `node_modules/`
- `public/research/`, `private_data/`, proposal batches, exports, and checkpoints
- Python bytecode and cache directories

The private remote must be verified as `PRIVATE` before any source is pushed. The pushed
default branch will be `main`.

## Public repository removal

After the private repository has been cloned back and independently verified, remove the
entire `protected_phd_agent` directory from the public repository. Also remove ignore rules
that exist only for that directory while preserving unrelated homepage rules and user
changes. Commit and push this deletion normally to `main`.

This design does not rewrite the public repository's historical commits. Historical agent
source code therefore remains obtainable from old commits, but the audit found no real
Proposal bodies or ignored private research directories in that history. A future history
rewrite would require a separate explicit decision because it is disruptive and requires a
force-push.

## Cloudflare and automation continuity

The deployed Worker, Durable Object, KV namespace, bindings, and secrets remain unchanged.
Moving source repositories must not overwrite or reinitialize online state. Wrangler must
continue to target the existing Worker and bindings from the private repository.

Update the existing `Resume private proposals` heartbeat so that future code operations use
the new private checkout. Its privacy and quota-aware behavior remain unchanged. No deploy
or proposal append occurs until all current advisor IDs have exactly one validated proposal
and `missingTotal` is zero.

## Verification and rollback

Before the public deletion:

1. Confirm the GitHub repository is private and its default branch is `main`.
2. Confirm the subtree history is present and the current Research Proposal work is
   committed in the private repository.
3. Run the complete Vitest and Python suites from the private checkout.
4. Run the private briefing verifier, `git diff --check`, and Wrangler deploy dry-run.
5. Confirm no real proposal, evidence, export, or credential file is tracked.

After the public deletion, confirm that the public `main` tree no longer contains
`protected_phd_agent`, the homepage's unrelated files are unchanged, and the private clone
still passes verification.

The public deletion is reversible with a normal revert because history is not rewritten.
The private repository provides an independent verified copy before any removal occurs.

## Acceptance criteria

- `ShuoLv-agent-private` exists under the intended GitHub account and is private.
- The private repository contains the application history and all current Proposal feature
  code, but no real private content or credentials.
- The public repository's current `main` tree contains no `protected_phd_agent` directory.
- Existing Cloudflare data and bindings are unchanged.
- All verification commands pass from the private checkout.
- The daily Proposal continuation task targets the private repository workflow.
