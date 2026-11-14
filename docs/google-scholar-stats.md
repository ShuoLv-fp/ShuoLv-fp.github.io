# Google Scholar statistics

The **Get Citation Data** GitHub Actions workflow fetches public author profile
VAsm0T8AAAAJ every Monday at 01:17 UTC (09:17 Asia/Shanghai). Scheduled runs can
start later when GitHub is busy. This is a weekly snapshot. The workflow also
supports manual dispatch for an immediate refresh.

## Data flow

1. The Python crawler reads citation totals, h-index, and publication citations
   using scholarly.
2. It validates the author ID and metrics before writing JSON. A successful
   snapshot gets a timezone-aware UTC update timestamp.
3. Only a successful crawl publishes the two JSON files to the google-scholar-stats
   branch. A failed crawl leaves the previously published data unchanged.
4. Both homepages read GitHub Raw and, when enabled in site configuration,
   jsDelivr. They display the valid response with the newest update timestamp,
   regardless of response order. Browser cache is bypassed; upstream CDN caches
   can still lag.
5. The visible update date uses Asia/Shanghai. Snapshots over 10 days old are
   marked outdated, and a failed page load shows a temporary-unavailability message.

The data branch update does not require rebuilding Jekyll. A page refresh loads
the latest available snapshot. Page builds do not trigger extra crawls.

## Operations

- In repository Actions, select **Get Citation Data**. If disabled, choose
  **Enable workflow**, then **Run workflow** on main.
- Check **Check crawler dependencies and regressions**, **Fetch Google Scholar
  statistics**, and **Publish statistics**. A green run must produce a newer
  update timestamp in gs_data.json on the google-scholar-stats branch.
- The default profile needs no additional credential. The GOOGLE_SCHOLAR_ID
  secret can override the author ID. Publishing uses the built-in GITHUB_TOKEN
  with contents-write permission.
- GitHub can disable schedules in inactive public repositories. If a snapshot
  stops advancing, check that the workflow is enabled and inspect recent runs.
- A crawl has a five-minute step limit, a 20-second request timeout, and three
  library retries. Google Scholar can still block automated traffic; a failed
  run retains the old snapshot and the page eventually flags its age. Inspect
  the log and manually rerun once after a transient failure. Do not substitute
  another database's counts for Google Scholar's metrics.

## Dependency incident

The September 9, 2026 run failed during import because the bibtexparser.bibdatabase
module was missing. The workflow was manually disabled on September 10, leaving
the September 8 snapshot visible. scholarly 1.7.11 requires the bibtexparser v1
interface, so bibtexparser 1.4.4 is pinned explicitly. Keep the import smoke check
when upgrading either dependency.

## Local verification

Install crawler dependencies in an isolated environment, then run from the repo:

    python -m pip install -r google_scholar_crawler/requirements.txt
    python -c "from scholarly import scholarly; from bibtexparser.bibdatabase import BibDatabase"
    python -m unittest discover -s tests -p 'test_google_scholar_stats.py' -v
    node --test tests/js/google-scholar-stats.test.js

Tests cover invalid metrics preserving prior files, UTC timestamps, weekly
scheduling, stale CDN responses arriving in either order, failed sources,
malformed data, legitimate zero counts, and both language variants.
