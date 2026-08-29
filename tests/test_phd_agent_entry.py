from pathlib import Path
import json
import unittest


class PhdAgentEntryTests(unittest.TestCase):
    def test_both_lean_images_use_one_configured_protected_url(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        self.assertRegex(config, r"(?m)^phd_agent_url\s*:")
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn('href="{{ site.phd_agent_url }}"', text)
            self.assertEqual(1, text.count('href="{{ site.phd_agent_url }}"'))
            self.assertIn("[Lean](https://lean-lang.org/)", text)

    def test_private_directories_are_excluded_from_jekyll(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        for path in ("phd_application_agent", "phd-advisor-summary", "protected_phd_agent"):
            self.assertIn(f"  - {path}", config)

    def test_pages_gateway_forwards_to_private_worker(self):
        config = json.loads(
            Path("protected_phd_agent/pages-gateway/wrangler.jsonc").read_text(encoding="utf-8")
        )
        self.assertEqual("./dist", config["pages_build_output_dir"])
        self.assertEqual(
            [{"binding": "PHD_AGENT_SERVICE", "service": "shuo-phd-agent"}],
            config["services"],
        )
        gateway = Path(
            "protected_phd_agent/pages-gateway/dist/_worker.js"
        ).read_text(encoding="utf-8")
        self.assertIn("env.PHD_AGENT_SERVICE.fetch(request)", gateway)
        self.assertNotIn("WORKFLOW_PASSWORD", gateway)
        self.assertNotIn("faculty", gateway.lower())


if __name__ == "__main__":
    unittest.main()
