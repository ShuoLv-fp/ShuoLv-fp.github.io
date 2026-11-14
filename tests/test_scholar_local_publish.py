import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError


SCRIPT = Path("google_scholar_crawler/update_stats.py")


class LocalPublishTests(unittest.TestCase):
    def load_publisher(self):
        spec = importlib.util.spec_from_file_location("local_publish", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_cdn_refresh_purges_both_published_files(self):
        module = self.load_publisher()
        self.assertTrue(hasattr(module, "refresh_cdn"))
        with patch.object(module, "urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(b'{"status":"finished"}')) as request:
            self.assertTrue(module.refresh_cdn())
            self.assertEqual(request.call_count, 2)
            urls = [call.args[0] for call in request.call_args_list]
            for filename in module.FILES:
                self.assertTrue(any(url.endswith('/' + filename) for url in urls))

    def test_cdn_failure_does_not_undo_published_data(self):
        module = self.load_publisher()
        self.assertTrue(hasattr(module, "refresh_cdn"))
        with patch.object(module, "urlopen", side_effect=URLError("temporarily unavailable")):
            self.assertFalse(module.refresh_cdn())

    def test_publish_updates_only_stats_branch_and_preserves_newer_data(self):
        self.assertTrue(SCRIPT.exists(), "A local publisher is required for the weekly automation")
        spec = importlib.util.spec_from_file_location("local_publish", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, seed, results = root / "remote.git", root / "seed", root / "results"
            results.mkdir()

            def git(*args, cwd=None):
                return subprocess.run(["git", *args], cwd=cwd, check=True,
                                      capture_output=True, text=True).stdout.strip()

            git("init", "--bare", str(remote))
            git("init", "-b", "google-scholar-stats", str(seed))
            git("config", "user.name", "Test Author", cwd=seed)
            git("config", "user.email", "test@example.invalid", cwd=seed)
            (seed / "gs_data.json").write_text(json.dumps({"updated": "2026-09-08T00:00:00+00:00"}))
            (seed / "gs_data_shieldsio.json").write_text('{}')
            git("add", ".", cwd=seed)
            git("commit", "-m", "Seed", cwd=seed)
            git("remote", "add", "origin", str(remote), cwd=seed)
            git("push", "origin", "google-scholar-stats", cwd=seed)
            git("branch", "main", cwd=seed)
            git("push", "origin", "main", cwd=seed)
            main_sha = git("rev-parse", "refs/heads/main", cwd=remote)
            data = {"scholar_id": "VAsm0T8AAAAJ", "citedby": 32, "hindex": 2,
                    "updated": "2026-11-14T02:44:18+00:00"}
            (results / "gs_data.json").write_text(json.dumps(data))
            (results / "gs_data_shieldsio.json").write_text(json.dumps({"message": "32"}))
            identity = {"GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                        "GIT_COMMITTER_NAME": "Test Author", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
            with patch.dict("os.environ", identity):
                self.assertTrue(module.publish_results(results, str(remote)))
                published_sha = git("rev-parse", "refs/heads/google-scholar-stats", cwd=remote)
                self.assertEqual(json.loads(git("show", "google-scholar-stats:gs_data.json", cwd=remote)), data)
                self.assertFalse(module.publish_results(results, str(remote)))
                data["updated"] = "2026-10-01T00:00:00+00:00"
                (results / "gs_data.json").write_text(json.dumps(data))
                self.assertFalse(module.publish_results(results, str(remote)))
                self.assertEqual(git("rev-parse", "refs/heads/google-scholar-stats", cwd=remote), published_sha)
            self.assertEqual(git("rev-parse", "refs/heads/main", cwd=remote), main_sha)


if __name__ == "__main__":
    unittest.main()
