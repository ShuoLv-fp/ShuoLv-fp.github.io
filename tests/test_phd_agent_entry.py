from pathlib import Path
import unittest

from tests.test_ewu_ultralow_field_mri import parse_top_level_config


class PhdAgentEntryTests(unittest.TestCase):
    def test_both_skills_toolkits_preserve_direct_lean_links(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn('<a href="https://lean-lang.org/">Lean</a>', text)

    def test_private_directories_are_excluded_from_jekyll(self):
        config = parse_top_level_config(Path("_config.yml").read_text(encoding="utf-8"))
        for path in ("phd_application_agent", "phd-advisor-summary", "protected_phd_agent"):
            self.assertIn(path, config["exclude"])

    def test_config_retains_the_deployed_private_gateway(self):
        config = parse_top_level_config(Path("_config.yml").read_text(encoding="utf-8"))
        self.assertEqual(
            "https://shuo-phd-agent-gateway.pages.dev", config["phd_agent_url"]
        )
        self.assertFalse(Path("protected_phd_agent").exists())


if __name__ == "__main__":
    unittest.main()
