# Google Scholar statistics

A Codex local automation fetches public author profile VAsm0T8AAAAJ every Monday
at 09:17 Asia/Shanghai. The computer must be online and Codex available to run the
automation. This is a weekly snapshot. The GitHub Actions workflow is retained
for manual diagnostics only: two hosted-runner attempts on November 14, 2026
received HTTP 403 from Google Scholar, while local fetches succeeded.

## Data flow

1. The Python crawler reads citation totals, h-index, and publication citations
   using scholarly.
2. It validates the author ID and metrics before writing JSON. A successful
   snapshot gets a timezone-aware UTC update timestamp.
3. The local update_stats.py wrapper runs the crawler with a three-minute limit,
   then publishes only the two JSON files in a temporary clone of the
   google-scholar-stats branch. It skips equal or older snapshots and uses a
   normal push so concurrent updates are never force-overwritten. A failed crawl
   leaves previously published data unchanged. The main checkout is not changed.
4. Both homepages read GitHub Raw and, when enabled in site configuration,
   jsDelivr. They display the valid response with the newest update timestamp,
   regardless of response order. Browser cache is bypassed; upstream CDN caches
   can still lag.
5. The visible update date uses Asia/Shanghai. Snapshots over 10 days old are
   marked outdated, and a failed page load shows a temporary-unavailability message.

The data branch update does not require rebuilding Jekyll. A page refresh loads
the latest available snapshot. Page builds do not trigger extra crawls.

## Operations

- The Codex automation **每周更新 Google Scholar 引用数据** runs the local wrapper
  using the isolated environment at google_scholar_crawler/.venv. Publishing uses
  the existing Git credential helper; no credential is written to source files.
- For an immediate update, run from the repository root:

      google_scholar_crawler/.venv/bin/python google_scholar_crawler/update_stats.py --publish

- Omitting --publish checks a live fetch without changing the published branch.
  A successful update must produce a newer timestamp in gs_data.json on the
  google-scholar-stats branch. The automation checks that value after publishing.
- The local publisher is restricted to author VAsm0T8AAAAJ. Google Scholar can
  still reject traffic; a failed run keeps the old snapshot and the page flags
  its age after 10 days. Inspect the log and retry once after a transient failure.
  Do not substitute another database's counts for Google Scholar's metrics.
- For optional cloud diagnostics, repository Actions still offers **Get Citation
  Data** with manual dispatch. It has no scheduled trigger, because this runner
  was blocked. Its publish token and permissions remain unchanged.
- An always-on update independent of this computer would require an accessible
  self-hosted runner or a configured Scholar data provider. Neither is required
  or provisioned for the current local schedule.

## Dependency incident

The September 9, 2026 run failed during import because the bibtexparser.bibdatabase
module was missing. The workflow was manually disabled on September 10, leaving
the September 8 snapshot visible. scholarly 1.7.11 requires the bibtexparser v1
interface, so bibtexparser 1.4.4 is pinned explicitly. Keep the import smoke check
when upgrading either dependency.

After fixing that dependency, hosted runs on November 14 logged repeated Google
Scholar HTTP 403 responses and timed out. The local environment fetched 32
citations and h-index 2 successfully, so weekly execution moved to this computer.

## Local verification

Install crawler dependencies in an isolated environment, then run from the repo:

    python -m pip install -r google_scholar_crawler/requirements.txt
    python -c "from scholarly import scholarly; from bibtexparser.bibdatabase import BibDatabase"
    python -m unittest discover -s tests -p 'test_google_scholar_stats.py' -v
    python -m unittest discover -s tests -p 'test_scholar_local_publish.py' -v
    node --test tests/js/google-scholar-stats.test.js

Tests cover invalid metrics preserving prior files, UTC timestamps, manual-only
cloud execution, stale CDN responses arriving in either order, failed sources,
malformed data, legitimate zero counts, both language variants, and publishing
to an isolated Git remote without changing main or overwriting newer snapshots.
