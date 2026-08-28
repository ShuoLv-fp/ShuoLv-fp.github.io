import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from protected_phd_agent.scripts.prepare_private_migration import prepare
from protected_phd_agent.scripts.verify_private_migration import verify_seed
from protected_phd_agent.scripts.verify_rewritten_history import verify_history


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class MigrationTests(unittest.TestCase):
    def make_source(self, root):
        source = root / "source"
        (source / "data").mkdir(parents=True)
        (source / "web").mkdir()
        (source / "web" / "index.html").write_text("<h1>Local workflow</h1>", encoding="utf-8")
        write_json(source / "data" / "profile.json", {"identity": {"name": "Synthetic Applicant"}})
        write_json(source / "data" / "faculty.json", [
            {"id": "fac_1", "name": "Synthetic Advisor", "display_name": "Synthetic Advisor"}
        ])
        write_json(source / "data" / "programs.json", [])
        write_json(source / "data" / "applications.json", [])
        write_json(source / "data" / "artifacts.json", [
            {"id": "art_1", "subject": "Synthetic draft subject", "content": "Synthetic draft body"}
        ])
        return source

    def test_prepare_copies_records_and_emits_hash_manifest_without_plaintext_terms(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = self.make_source(root)
            private = root / "private"

            manifest = prepare(source, private)

            self.assertEqual(1, manifest["counts"]["faculty"])
            self.assertEqual(1, manifest["counts"]["artifacts"])
            self.assertNotIn("Synthetic Advisor", json.dumps(manifest))
            self.assertNotIn("Synthetic draft subject", json.dumps(manifest))
            self.assertTrue((private / "local-app-snapshot" / "web" / "index.html").exists())
            verify_seed(private / "cloudflare-seed.json", private / "manifest.json")

    def test_history_verifier_rejects_removed_paths_without_printing_private_text(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = self.make_source(root)
            private = root / "private"
            prepare(source, private)
            repo = root / "repo"
            path = repo / "phd_application_agent" / "data"
            path.mkdir(parents=True)
            (path / "faculty.json").write_text("Synthetic Advisor", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=repo, check=True)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

            with self.assertRaisesRegex(RuntimeError, "removed path"):
                verify_history(repo, private / "manifest.json")


if __name__ == "__main__":
    unittest.main()
