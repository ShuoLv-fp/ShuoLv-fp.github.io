import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = REPOSITORY_ROOT / "protected_phd_agent"
VALIDATOR = AGENT_ROOT / "scripts" / "validate_research_group_batch.mjs"
UPLOADER = AGENT_ROOT / "scripts" / "append_research_group_batch.py"
NODE_BINARY = os.environ.get("NODE_BINARY", "node")


def synthetic_faculty(index=0, **overrides):
    suffix = f"{index:012x}"
    record = {
        "id": f"fac_{suffix}",
        "name": f"Synthetic Researcher {index}",
        "display_name": f"Synthetic Researcher {index}",
        "institution": "Example Institute of Technology",
        "institution_short": "EIT",
        "department": "Department of Computational Science",
        "country": "United Kingdom",
        "region": "Europe",
        "entry_type": "research_group",
        "homepage_url": f"https://example.edu/lab/{index}",
        "word_homepage_url": f"https://example.edu/lab/{index}",
        "research_area": "Agent/AI4Science",
        "research_summary": "Autonomous agents for scientific reasoning and discovery.",
        "keywords": ["llm agents", "ai for science"],
        "evidence": [{
            "title": "Official research group page",
            "url": f"https://example.edu/lab/{index}",
            "checked_on": "2026-09-07T00:00:00Z",
            "note": "Official institutional page confirms the current research focus.",
        }],
        "fit": {
            "total": 86,
            "confidence": "high",
            "dimensions": [{
                "name": "AI4Science / LLM Agents",
                "matched_terms": ["llm agents"],
            }],
        },
        "match_analysis": {
            "summary": "Strong overlap with agentic scientific reasoning."
        },
        "email_addressee": "Professor Researcher",
        "source_document": "Independent official-web research",
    }
    record.update(overrides)
    return record


def run_validator(batch_path, existing_path, minimum):
    return subprocess.run(
        [
            NODE_BINARY,
            str(VALIDATOR),
            "--batch",
            str(batch_path),
            "--existing",
            str(existing_path),
            "--minimum",
            str(minimum),
        ],
        cwd=AGENT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class BatchValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.existing = self.root / "existing.json"
        self.existing.write_text(json.dumps({"faculty": []}), encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def write_batch(self, records):
        path = self.root / "batch.json"
        path.write_text(json.dumps({"faculty": records}), encoding="utf-8")
        return path

    def test_validates_one_hundred_unique_records_without_printing_record_data(self):
        batch = self.write_batch([synthetic_faculty(index) for index in range(100)])

        completed = run_validator(batch, self.existing, 100)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual(summary["submitted"], 100)
        self.assertEqual(summary["validNew"], 100)
        self.assertEqual(summary["localDuplicates"], 0)
        self.assertEqual(summary["countryCounts"], {"United Kingdom": 100})
        self.assertEqual(summary["categoryCounts"], {"Agent/AI4Science": 100})
        self.assertEqual(summary["scoreRange"], {"min": 86, "max": 86})
        self.assertNotIn("Synthetic Researcher", completed.stdout)
        self.assertNotIn("example.edu", completed.stdout)

    def test_fails_when_valid_new_count_is_below_minimum(self):
        batch = self.write_batch([synthetic_faculty(1)])

        completed = run_validator(batch, self.existing, 2)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("valid new record count 1 is below required minimum 2", completed.stderr)
        self.assertNotIn("Synthetic Researcher", completed.stderr)

    def test_fails_on_forbidden_country_without_printing_the_record(self):
        batch = self.write_batch([synthetic_faculty(1, country="United States")])

        completed = run_validator(batch, self.existing, 1)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("country is not eligible", completed.stderr)
        self.assertNotIn("Synthetic Researcher", completed.stderr)

    def test_reports_existing_seed_duplicates_as_aggregates(self):
        duplicate = synthetic_faculty(9)
        self.existing.write_text(json.dumps({"faculty": [duplicate]}), encoding="utf-8")
        batch = self.write_batch([duplicate])

        completed = run_validator(batch, self.existing, 0)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual(summary["validNew"], 0)
        self.assertEqual(summary["localDuplicates"], 1)
        self.assertNotIn("Synthetic Researcher", completed.stdout)


class _AppendHandler(http.server.BaseHTTPRequestHandler):
    received = None

    def do_POST(self):
        length = int(self.headers["content-length"])
        body = self.rfile.read(length)
        type(self).received = {
            "path": self.path,
            "authorization": self.headers.get("authorization"),
            "body": json.loads(body),
        }
        payload = json.dumps({
            "revision": 7,
            "submitted": 1,
            "appended": 1,
            "skipped": 0,
            "previousFacultyTotal": 93,
            "facultyTotal": 94,
            "featuredTotal": 29,
            "artifactTotal": 28,
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format_string, *args):
        return


class BatchUploaderTests(unittest.TestCase):
    def test_posts_to_the_append_route_without_printing_secrets_or_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch = root / "batch.json"
            batch.write_text(
                json.dumps({"faculty": [synthetic_faculty(1)]}),
                encoding="utf-8",
            )
            secret = root / "secret"
            secret.write_text("synthetic-secret-value-with-32-bytes\n", encoding="utf-8")
            secret.chmod(0o600)

            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _AppendHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                completed = subprocess.run(
                    [
                        "python3",
                        str(UPLOADER),
                        "--url",
                        f"http://127.0.0.1:{server.server_port}",
                        "--batch",
                        str(batch),
                        "--secret-file",
                        str(secret),
                        "--allow-http-localhost",
                    ],
                    cwd=AGENT_ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(_AppendHandler.received["path"], "/api/admin/faculty/append")
        self.assertEqual(
            _AppendHandler.received["authorization"],
            "Bearer synthetic-secret-value-with-32-bytes",
        )
        self.assertEqual(len(_AppendHandler.received["body"]["faculty"]), 1)
        output = json.loads(completed.stdout)
        self.assertEqual(output["appended"], 1)
        self.assertEqual(output["facultyTotal"], 94)
        self.assertNotIn("synthetic-secret-value-with-32-bytes", completed.stdout + completed.stderr)
        self.assertNotIn("Synthetic Researcher", completed.stdout + completed.stderr)

    def test_rejects_secret_files_with_unsafe_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch = root / "batch.json"
            batch.write_text(json.dumps({"faculty": [synthetic_faculty(1)]}), encoding="utf-8")
            secret = root / "secret"
            secret.write_text("synthetic-secret-value-with-32-bytes\n", encoding="utf-8")
            secret.chmod(0o644)

            completed = subprocess.run(
                [
                    "python3",
                    str(UPLOADER),
                    "--url",
                    "https://example.invalid",
                    "--batch",
                    str(batch),
                    "--secret-file",
                    str(secret),
                ],
                cwd=AGENT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("secret file permissions must be 0600", completed.stderr)
        self.assertNotIn("synthetic-secret-value-with-32-bytes", completed.stderr)


if __name__ == "__main__":
    unittest.main()
