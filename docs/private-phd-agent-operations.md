# Private PhD Agent Operations

This runbook operates the password-protected Cloudflare Worker without placing production records or secret values in Git. Run Worker commands from `protected_phd_agent/`. Never paste secret values into source files, screenshots, issue trackers, or command arguments.

## Local recovery assets

- Ignored migration bundle: `phd_application_agent/private_data/`
- Redundant private copy: `../ShuoLv-fp.github.io-private-agent-backup/`
- Pre-cleanup Git bundle: `../ShuoLv-fp.github.io-before-private-agent.bundle`

Keep both external files outside any public repository and include them in the normal encrypted computer backup.

## Authenticate Wrangler

```bash
pnpm exec wrangler whoami
pnpm exec wrangler login
pnpm exec wrangler whoami
```

Complete Cloudflare authorization in the browser yourself. Do not send account credentials to another person or process.

## Configure or rotate secrets

Wrangler prompts without storing the value in the repository:

```bash
pnpm exec wrangler secret put WORKFLOW_PASSWORD
pnpm exec wrangler secret put SESSION_SECRET
pnpm exec wrangler secret put RATE_LIMIT_SECRET
pnpm exec wrangler secret put MIGRATION_SECRET
```

Use the chosen workflow password only for `WORKFLOW_PASSWORD`. Generate the other three as independent high-entropy values. Rotating `SESSION_SECRET` invalidates every existing browser session. Rotating only `WORKFLOW_PASSWORD` changes future login checks but does not revoke an already valid session.

## Test and deploy

```bash
pnpm test
pnpm run check
pnpm exec wrangler deploy
```

The login shell is data-free. Confirm `/api/bootstrap` returns HTTP 401 without a session before importing production data.

## One-time production import

First verify the local bundle:

```bash
python3 scripts/verify_private_migration.py \
  --seed ../phd_application_agent/private_data/cloudflare-seed.json \
  --manifest ../phd_application_agent/private_data/manifest.json
```

In a private interactive terminal, read the migration secret without echo and import once:

```bash
read -s "PHD_MIGRATION_SECRET?Migration secret: "
export PHD_MIGRATION_SECRET
curl --fail-with-body --request POST "$PHD_AGENT_URL/api/admin/import" \
  --header "Authorization: Bearer $PHD_MIGRATION_SECRET" \
  --header "Content-Type: application/json" \
  --data-binary @../phd_application_agent/private_data/cloudflare-seed.json
unset PHD_MIGRATION_SECRET
```

A successful first import returns revision `1`; every later import to the same coordinator returns HTTP 409. Verify remote collection hashes without printing records:

```bash
python3 scripts/verify_private_migration.py \
  --seed ../phd_application_agent/private_data/cloudflare-seed.json \
  --manifest ../phd_application_agent/private_data/manifest.json \
  --remote "$PHD_AGENT_URL"
```

The verifier prompts privately for the workflow password.

## Export and regular backup

Use **Export backup** inside the authenticated page and move the downloaded JSON into encrypted local storage. The export includes the authoritative revision and all collections. Do not add it to this repository.

After an important editing session, compare the exported collection counts with the private manifest and retain at least two dated encrypted copies.

## Restore into an empty coordinator

The import endpoint intentionally refuses to overwrite an initialized coordinator. For disaster recovery:

1. Preserve an authenticated export and the latest KV snapshot.
2. Deploy a recovery Worker with a new name and a new Durable Object namespace.
3. Configure four fresh secrets for the recovery Worker.
4. Import the verified export through its one-time import route.
5. Run the remote hash verifier.
6. Only after verification, update the homepage Worker URL and retire the damaged deployment.

Never add a public reset or arbitrary overwrite endpoint to make restoration faster.

## Worker rollback

List deployed versions, inspect the intended target, and roll back only application code:

```bash
pnpm exec wrangler versions list
pnpm exec wrangler rollback
```

A code rollback does not roll back Durable Object data. Export current data before rolling back and re-run login, bootstrap, edit-conflict, export, and logout checks afterward.

## Session invalidation and logout

- Normal case: click **Lock** in the application; the server deletes that session record.
- Lost or shared device: rotate `SESSION_SECRET` and redeploy; all signed session cookies become invalid.
- Suspected password disclosure: rotate both `WORKFLOW_PASSWORD` and `SESSION_SECRET`, then review Cloudflare request logs for unusual rate-limit activity without enabling request-body logging.

## Git history cleanup recovery

Before history cleanup, verify the external bundle:

```bash
git bundle verify ../ShuoLv-fp.github.io-before-private-agent.bundle
```

After the approved rewrite, every collaborator must delete or archive the old clone and make a fresh clone. Do not merge or push branches created from the old object history. The external bundle is private recovery material because it intentionally retains the removed history.

Independent forks, old clones, and third-party caches are outside the repository owner's direct control; history rewriting removes reachable data from the published repository but cannot erase those copies.
