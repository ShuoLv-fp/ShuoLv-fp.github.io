from pathlib import Path
import unittest


class GoogleScholarStatsTests(unittest.TestCase):
    def test_crawler_workflow_can_publish_results(self):
        workflow = Path(
            ".github/workflows/google_scholar_crawler.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertRegex(
            workflow,
            r"(?s)name: Fetch Google Scholar statistics\s+"
            r"working-directory: google_scholar_crawler\s+"
            r"run: python main\.py",
        )

    def test_crawler_uses_current_scholarly_release(self):
        requirements = Path(
            "google_scholar_crawler/requirements.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("scholarly==1.7.11", requirements)
        self.assertNotIn("scholarly==1.5.1", requirements)

    def test_page_falls_back_to_raw_github_stats(self):
        script = Path(
            "_includes/fetch_google_scholar_stats.html"
        ).read_text(encoding="utf-8")

        self.assertIn("cdn.jsdelivr.net", script)
        self.assertIn("raw.githubusercontent.com", script)
        self.assertIn(".fail(function", script)


if __name__ == "__main__":
    unittest.main()
