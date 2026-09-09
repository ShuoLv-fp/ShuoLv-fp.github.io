from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/paper-feed.yml"


class PaperFeedWorkflowTests(unittest.TestCase):
    def workflow(self):
        return WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_has_safe_triggers_permissions_and_concurrency(self):
        text = self.workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("schedule:", text)
        self.assertIn('cron: "17 1 * * *"', text)
        self.assertNotIn("pull_request:", text)
        self.assertIn("contents: write", text)
        self.assertIn("group: paper-feed-update", text)
        self.assertIn("cancel-in-progress: false", text)

    def test_manual_run_defaults_to_thirty_day_preview(self):
        text = self.workflow()
        self.assertRegex(text, r"(?s)lookback_days:\s+description:.*?type: choice.*?default: \"30\".*?options:\s+- \"7\"\s+- \"30\"")
        self.assertRegex(text, r"(?s)publish:\s+description:.*?type: boolean.*?default: false")
        self.assertIn("github.event_name == 'schedule'", text)

    def test_toolchain_tests_build_and_private_secrets_are_wired(self):
        text = self.workflow()
        for marker in (
            'python-version: "3.11"',
            'node-version: "20"',
            "ruby-version: \"3.1\"",
            "pip install --requirement paper_feed/requirements.txt",
            "python -m unittest discover",
            "node --test tests/js/*.test.js",
            "bundle exec jekyll build",
        ):
            self.assertIn(marker, text)
        for name in ("FOXMAIL_USERNAME", "FOXMAIL_IMAP_AUTH_CODE", "DEEPSEEK_API_KEY"):
            self.assertIn("${{ secrets." + name + " }}", text)
        self.assertNotIn("sk-", text)

    def test_preview_artifact_is_short_lived_and_publish_commit_is_restricted(self):
        text = self.workflow()
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("retention-days: 3", text)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.publish == false", text)
        self.assertIn("git add -- assets/data/paper-feed.json paper_feed/state/retries.json", text)
        self.assertIn("git rebase --abort", text)
        self.assertNotIn("--force", text)

    def test_documentation_names_routes_data_and_safe_secret_setup(self):
        guide = (ROOT / "docs/paper-feed-operations.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for marker in ("/paper-feed/", "/zh/paper-feed/", "assets/data/paper-feed.json", "paper-feed.yml"):
            self.assertIn(marker, readme)
        for marker in ("FOXMAIL_USERNAME", "FOXMAIL_IMAP_AUTH_CODE", "DEEPSEEK_API_KEY", "撤销", "不要粘贴"):
            self.assertIn(marker, guide)


if __name__ == "__main__":
    unittest.main()
