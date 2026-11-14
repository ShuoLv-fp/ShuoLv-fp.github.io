from pathlib import Path
import json
import os
import runpy
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class GoogleScholarStatsTests(unittest.TestCase):
    def test_crawler_workflow_can_publish_results(self):
        workflow = Path(
            ".github/workflows/google_scholar_crawler.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn('cron: "17 1 * * 1"', workflow)
        fetch_workflow = Path(".github/workflows/scholar_fetch.yaml").read_text()
        self.assertIn('SCHOLAR_FETCH_MODE: direct', fetch_workflow)
        self.assertIn('runner: ubuntu-24.04-arm', workflow)
        self.assertIn("needs.primary.outputs.available != 'true'", workflow)
        self.assertIn("needs.primary.outputs.available == 'true' || needs.fallback.outputs.available == 'true'", workflow)
        self.assertIn("needs.retry.outputs.available == 'true'", workflow)
        self.assertIn('test "$AVAILABLE" = "true"', workflow)
        self.assertIn('actions/download-artifact@v4', workflow)
        self.assertNotIn('continue-on-error:', workflow)
        self.assertNotIn('if: false', workflow)
        self.assertNotIn('--force', workflow)
        self.assertNotIn("page_build:", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn('if python main.py; then', fetch_workflow)
        self.assertIn("steps.fetch.outputs.available == 'true'", fetch_workflow)
        self.assertIn('if-no-files-found: error', fetch_workflow)

    def test_crawler_uses_current_scholarly_release(self):
        requirements = Path(
            "google_scholar_crawler/requirements.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("scholarly==1.7.11", requirements)
        self.assertNotIn("scholarly==1.5.1", requirements)

    def test_bibtexparser_keeps_the_api_required_by_scholarly(self):
        requirements = Path("google_scholar_crawler/requirements.txt").read_text()
        self.assertIn("bibtexparser==1.4.4", requirements)

    def test_page_checks_both_sources_for_fresh_stats(self):
        script = Path(
            "_includes/fetch_google_scholar_stats.html"
        ).read_text(encoding="utf-8")

        self.assertIn("cdn.jsdelivr.net", script)
        self.assertIn("raw.githubusercontent.com", script)
        self.assertIn("cache: false", script)
        self.assertIn("timeout:", script)

    def test_both_languages_hide_scholar_update_date(self):
        for path in ("_pages/includes/pub.md", "_pages/includes/zh/pub.md"):
            self.assertNotIn('id="scholar_updated"', Path(path).read_text())

    def test_weekly_update_documents_cloud_execution(self):
        guide = Path("docs/google-scholar-stats.md").read_text()
        self.assertIn("GitHub Actions", guide)
        self.assertIn("09:17 Asia/Shanghai", guide)
        self.assertIn("update_stats.py", guide)


class CrawlerOutputTests(unittest.TestCase):
    def run_crawler(self, author, directory):
        client = Mock()
        client.search_author_id.return_value = author
        client.fill.return_value = author
        module = types.ModuleType("scholarly")
        module.scholarly = client
        script = Path("google_scholar_crawler/main.py").resolve()
        original = Path.cwd()
        try:
            os.chdir(directory)
            with patch.dict("sys.modules", {"scholarly": module}), patch.dict(
                os.environ, {"GOOGLE_SCHOLAR_ID": "test-author", "SCHOLAR_FETCH_MODE": "scholarly"}
            ):
                runpy.run_path(str(script), run_name="__main__")
        finally:
            os.chdir(original)

    def author(self):
        return {
            "scholar_id": "test-author", "name": "Test Author",
            "citedby": 42, "hindex": 3,
            "publications": [{"author_pub_id": "test-author:paper", "num_citations": 42}],
        }

    def test_success_publishes_metrics_with_timezone_and_publication_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_crawler(self.author(), directory)
            data = json.loads((Path(directory) / "results/gs_data.json").read_text())
            self.assertEqual(data["citedby"], 42)
            self.assertEqual(data["hindex"], 3)
            self.assertTrue(data["updated"].endswith("+00:00"))
            self.assertIn("test-author:paper", data["publications"])
            badge = json.loads((Path(directory) / "results/gs_data_shieldsio.json").read_text())
            self.assertEqual(badge["message"], "42")

    def test_invalid_metrics_preserve_last_successful_files(self):
        for change in ({"hindex": None}, {"citedby": -1}, {"hindex": True}, {"scholar_id": "wrong-author"}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "results"
                output.mkdir()
                snapshot = output / "gs_data.json"
                snapshot.write_text('{"previous": true}')
                badge = output / "gs_data_shieldsio.json"
                badge.write_text('{"previous": true}')
                with self.assertRaises(ValueError):
                    self.run_crawler({**self.author(), **change}, directory)
                self.assertEqual(snapshot.read_text(), '{"previous": true}')
                self.assertEqual(badge.read_text(), '{"previous": true}')


if __name__ == "__main__":
    unittest.main()
