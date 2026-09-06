# Private faculty batch operations

The faculty list is private application data. Never place research batches, exports,
session keys, migration secrets, or the current production snapshot in this repository.

## Validate a batch

Run the validator before any upload. Both JSON files must live outside the Git
repository. The command prints aggregate counts only.

```sh
node scripts/validate_research_group_batch.mjs \
  --batch /absolute/private/path/research-group-batch.json \
  --existing /absolute/private/path/current-snapshot.json \
  --minimum 100
```

The validator rejects malformed records, US/Canada entries, duplicate IDs, duplicate
canonical homepages, duplicate name-and-institution pairs, and a batch that falls below
the requested number of new records.

## Append to production

The production operation is append-only and atomic. It reads the current live state,
deduplicates the submitted records against that state, appends valid new entries, and
increments the data revision once. A rejected record prevents the entire batch from
being written.

Store the migration secret in a mode-0600 file outside the repository, then run:

```sh
python3 scripts/append_research_group_batch.py \
  --url https://your-private-site.example \
  --batch /absolute/private/path/research-group-batch.json \
  --secret-file /absolute/private/path/migration-secret
```

The uploader requires HTTPS except for explicit localhost tests and reports aggregate
totals only. Re-running the same batch is safe: already-present records are skipped.
Newly appended records remain unfeatured so the existing hand-curated featured list is
unchanged.

## Post-upload checks

1. Run the uploader a second time and confirm that it appends zero records.
2. Sign in to the private site and confirm the faculty total, filters, and a sample of
   official homepage links.
3. Confirm that featured faculty and artifacts are unchanged.
4. Delete the temporary local secret file after the checks; retain the private research
   batch only in the approved backup location.

If an upload fails, do not replace production with an older local snapshot. Fix the
batch or deployment and retry the append operation against the live state.
