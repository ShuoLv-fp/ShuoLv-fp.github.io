# Google Scholar statistics

GitHub Actions fetches public author profile VAsm0T8AAAAJ every Monday
at 09:17 Asia/Shanghai (01:17 UTC), with manual dispatch also available.
The computer and Codex do not need to remain running. This is a weekly snapshot.
Direct access from shared hosted IPs remains intermittent: some runs succeeded,
but later ARM and Windows runners were all blocked. A direct-only configuration
is best effort, not a verified reliability fix.

For a provider-backed configuration, add a repository Actions secret named
SERPAPI_API_KEY. The crawler then prefers SerpAPI's google_scholar_author endpoint
with no_cache=true and validates the returned author ID and all-time metrics.
This optional path is tested with the documented response schema, but needs a
real credential and successful live run before it can be considered accepted.
See https://serpapi.com/google-scholar-author-api for service and account details.

## Data flow

1. The cloud crawler reads the public profile using bounded curl requests and a
   browser-compatible curl_cffi fallback. Each transport gets at most three
   attempts. Total citations and h-index come from the profile's metrics table.
   An ARM Linux hosted runner is primary; Windows is used only if it cannot obtain
   a verified profile. A final ARM retry allocates a fresh hosted runner when both
   earlier attempts are blocked. Both hosted networks passed live fetching on November 14.
2. It validates the canonical author ID, name, metrics, and publication IDs before
   writing JSON. An HTTP 200 block page is rejected. A successful snapshot gets
   an internal UTC timestamp. The publication list records whether it is complete;
   profile-wide metrics are independent of publication pagination.
3. The workflow publishes only the two JSON files to google-scholar-stats using
   a normal push. A runner's access refusal triggers the fallback, and the final
   publish gate requires a verified snapshot artifact from this workflow run.
   If all three runners fail, the overall workflow fails and published data stays
   unchanged. No old snapshot is stamped as fresh. Publishing requests a CDN purge.
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
- The previous local Codex automation is paused to avoid duplicate weekly runs.
  The update_stats.py utility remains for manual recovery:

      google_scholar_crawler/.venv/bin/python google_scholar_crawler/update_stats.py --publish

- Omitting --publish checks a live fetch without changing the published branch.
  A successful update must produce a newer timestamp in gs_data.json on the
  google-scholar-stats branch. The automation checks that value after publishing.
- The local publisher is restricted to author VAsm0T8AAAAJ. Google Scholar can
  still reject traffic; a failed run keeps the old snapshot. Inspect the internal
  JSON timestamp and workflow log, then retry once after a transient failure.
  Do not substitute another database's counts for Google Scholar's metrics.
- Cloud publishing uses the existing GITHUB_TOKEN. Direct fetching needs no API
  credential; the optional provider uses only SERPAPI_API_KEY from Actions Secrets.
  API URLs containing the credential are never printed. Google and the provider remain external dependencies;
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
