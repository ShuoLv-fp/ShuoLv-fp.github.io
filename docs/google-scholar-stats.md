# Google Scholar statistics

GitHub Actions fetches public author profile VAsm0T8AAAAJ every Monday
at 09:17 Asia/Shanghai (01:17 UTC), with manual dispatch also available.
The computer and Codex do not need to remain running. This is a weekly snapshot.

## Data flow

1. The cloud crawler reads the public profile using bounded curl requests and a
   browser-compatible curl_cffi fallback. Each transport gets at most three
   attempts. Total citations and h-index come from the profile's metrics table.
2. It validates the canonical author ID, name, metrics, and publication IDs before
   writing JSON. An HTTP 200 block page is rejected. A successful snapshot gets
   an internal UTC timestamp. The publication list records whether it is complete;
   profile-wide metrics are independent of publication pagination.
3. The workflow publishes only the two JSON files to google-scholar-stats using
   a normal push. A failed crawl leaves published data unchanged and fails visibly;
   no old snapshot is stamped as fresh. After publishing, it requests a CDN purge.
   A cache-purge failure is reported without reverting the successful publication.
4. Both homepages read GitHub Raw and, when enabled in site configuration,
   jsDelivr. They display the valid response with the newest update timestamp,
   regardless of response order. Browser cache is bypassed; upstream CDN caches
   can still lag.
5. The website displays citation metrics without an update date. Internal
   timestamps remain available in the JSON and workflow summary for verification.

The data branch update does not require rebuilding Jekyll. A page refresh loads
the latest available snapshot. Page builds do not trigger extra crawls.

## Operations

- For an immediate cloud update, select Actions > **Get Citation Data** >
  **Run workflow** on main. Check the fetch, publish, and summary steps. A green
  run must advance the internal timestamp in gs_data.json on google-scholar-stats.
- The previous local Codex automation is paused after cloud acceptance to avoid
  duplicate weekly runs. The update_stats.py utility remains for manual recovery:

      google_scholar_crawler/.venv/bin/python google_scholar_crawler/update_stats.py --publish

- Omitting --publish checks a live fetch without changing the published branch.
  A successful update must produce a newer timestamp in gs_data.json on the
  google-scholar-stats branch. The automation checks that value after publishing.
- The local publisher is restricted to author VAsm0T8AAAAJ. Google Scholar can
  still reject traffic; a failed run keeps the old snapshot and the page flags
  its age after 10 days. Inspect the log and retry once after a transient failure.
  Do not substitute another database's counts for Google Scholar's metrics.
- Cloud publishing uses the existing GITHUB_TOKEN. No paid API, proxy credential,
  or local runner is required. Google's service remains an external dependency;
  failed validation cannot be converted to a successful run with stale values.

## Dependency incident

The September 9, 2026 run failed during import because the bibtexparser.bibdatabase
module was missing. The workflow was manually disabled on September 10, leaving
the September 8 snapshot visible. scholarly 1.7.11 requires the bibtexparser v1
interface, so bibtexparser 1.4.4 is pinned explicitly. Keep the import smoke check
when upgrading either dependency.

After fixing that dependency, the scholarly cloud path repeatedly received HTTP
403 and stalled in session-recreation loops. Linux and macOS both reproduced the
block. A later Linux curl request returned a genuine profile with 32 citations and
h-index 2. Production now uses direct requests, bounded fallback, and explicit
validation. The previous local fallback is superseded by the cloud schedule.

## Local verification

Install crawler dependencies in an isolated environment, then run from the repo:

    python -m pip install -r google_scholar_crawler/requirements.txt
    python -c "from scholarly import scholarly; from bibtexparser.bibdatabase import BibDatabase"
    python -m unittest discover -s tests -p 'test_google_scholar_stats.py' -v
    python -m unittest discover -s tests -p 'test_scholar_cloud_fetch.py' -v
    python -m unittest discover -s tests -p 'test_scholar_local_publish.py' -v
    node --test tests/js/google-scholar-stats.test.js

Tests cover invalid metrics preserving prior files, UTC timestamps, weekly
cloud execution, stale CDN responses arriving in either order, failed sources,
malformed data, legitimate zero counts, hidden dates in both languages, and publishing
to an isolated Git remote without changing main or overwriting newer snapshots.
