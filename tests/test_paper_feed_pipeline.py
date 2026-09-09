from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from paper_feed.main import PipelineError, _invoke_summarizer, _sort_records, run_pipeline
from paper_feed.summarizer import summarize
from paper_feed.models import LocalizedSummary, PaperMetadata, PaperRecord, PaperSummary
from paper_feed.settings import Settings


FIXTURES = Path(__file__).parent / "fixtures"


class PaperFeedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        root = Path(self.directory.name)
        self.feed_path = root / "feed.json"
        self.retry_path = root / "retries.json"
        self.feed_path.write_text(
            '{"schema_version": 1, "generated_at": null, "timezone": "Asia/Shanghai", "papers": []}\n',
            encoding="utf-8",
        )
        self.retry_path.write_text('{"schema_version": 1, "retries": {}}\n', encoding="utf-8")
        self.messages = [(FIXTURES / "scholar_alert.txt.eml").read_bytes()]
        self.duplicate_messages = self.messages * 2
        self.settings = Settings()
        self.now = datetime(2026, 9, 10, 1, 2, 3, tzinfo=timezone.utc)

    def tearDown(self):
        self.directory.cleanup()

    @staticmethod
    def enricher(candidate):
        return PaperMetadata(
            title=candidate.title,
            authors=candidate.authors,
            venue=candidate.venue or "Synthetic Journal",
            year=candidate.year,
            canonical_url=candidate.canonical_url,
            doi="10.1000/synthetic",
            arxiv_id=None,
            abstract="Synthetic public abstract.",
            evidence_type="abstract",
        )

    @staticmethod
    def summarizer(metadata):
        return PaperSummary(
            relevance="high",
            en=LocalizedSummary("Synthetic conclusion.", ("Point one.", "Point two."), "A research connection.", ("Synthetic",)),
            zh=LocalizedSummary("合成结论。", ("要点一。", "要点二。"), "一项研究关联。", ("合成",)),
        )

    def invoke_pipeline(self, messages=None, **changes):
        return run_pipeline(
            self.settings, messages or self.messages, self.feed_path, self.retry_path,
            publish=changes.pop("publish", True), now=self.now,
            enricher=changes.pop("enricher", self.enricher),
            summarizer=changes.pop("summarizer", self.summarizer), **changes,
        )

    @staticmethod
    def alert_message(title, url, authors="Dana Placeholder", venue="Imaginary Computing Review"):
        return f"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - synthetic result
Date: Tue, 09 Sep 2026 09:00:00 +0000
Content-Type: text/plain; charset=UTF-8

{title}
{url}
{authors} - {venue}, 2026
Google Scholar: synthetic public evidence.
""".encode()

    def test_dry_run_never_changes_files_and_writes_sanitized_preview(self):
        before_feed = self.feed_path.read_bytes()
        before_retries = self.retry_path.read_bytes()
        preview_path = self.feed_path.parent / "preview.json"
        result = self.invoke_pipeline(publish=False, preview_path=preview_path)
        self.assertEqual(result.new, 1)
        self.assertEqual(self.feed_path.read_bytes(), before_feed)
        self.assertEqual(self.retry_path.read_bytes(), before_retries)
        preview = json.loads(preview_path.read_text(encoding="utf-8"))
        self.assertEqual(len(preview["papers"]), 1)
        self.assertNotIn("recipient", json.dumps(preview))

    def test_duplicate_alerts_publish_one_public_card_without_provenance(self):
        self.invoke_pipeline(messages=self.duplicate_messages)
        text = self.feed_path.read_text(encoding="utf-8")
        self.assertEqual(len(json.loads(text)["papers"]), 1)
        self.assertNotIn("subscription_author", text)
        self.assertNotIn("trigger_author", text)

    def test_one_paper_failure_does_not_block_other_paper(self):
        messages = [(FIXTURES / "scholar_alert.html.eml").read_bytes()]

        def flaky(candidate):
            if "Foundation" in candidate.title:
                raise RuntimeError("private error text")
            return self.enricher(candidate)

        result = self.invoke_pipeline(messages=messages, enricher=flaky)
        self.assertEqual(result.summarized, 1)
        self.assertEqual(result.deferred, 1)
        self.assertEqual(len(json.loads(self.feed_path.read_text())["papers"]), 1)

    def test_three_failed_runs_publish_metadata_only_and_later_runs_keep_retrying(self):
        def fails(_candidate):
            raise RuntimeError("private upstream text")

        for expected_attempts in (1, 2):
            result = self.invoke_pipeline(enricher=fails)
            self.assertEqual(result.deferred, 1)
            retries = json.loads(self.retry_path.read_text())["retries"]
            self.assertEqual(next(iter(retries.values()))["attempts"], expected_attempts)
        result = self.invoke_pipeline(enricher=fails)
        self.assertEqual(result.metadata_only, 1)
        paper = json.loads(self.feed_path.read_text())["papers"][0]
        self.assertEqual(paper["status"], "summary_unavailable")
        self.assertEqual(paper["evidence_type"], "unavailable")
        self.invoke_pipeline(enricher=fails)
        self.assertEqual(next(iter(json.loads(self.retry_path.read_text())["retries"].values()))["attempts"], 4)

    def test_pipeline_wide_parse_or_invalid_existing_feed_failure_preserves_both_files(self):
        for messages, feed in (
            ([(FIXTURES / "scholar_alert.html.eml").read_bytes().replace(b"https%3A%2F%2Fexample.invalid", b"http%3A%2F%2Fexample.invalid", 1)], None),
            (self.messages, '{"bad": true}\n'),
        ):
            with self.subTest(feed=feed):
                if feed:
                    self.feed_path.write_text(feed, encoding="utf-8")
                before_feed, before_retries = self.feed_path.read_bytes(), self.retry_path.read_bytes()
                with self.assertRaises(PipelineError):
                    self.invoke_pipeline(messages=messages)
                self.assertEqual(self.feed_path.read_bytes(), before_feed)
                self.assertEqual(self.retry_path.read_bytes(), before_retries)

    def test_failed_second_final_replace_restores_byte_identical_files(self):
        before_feed, before_retries = self.feed_path.read_bytes(), self.retry_path.read_bytes()
        real_replace = __import__("os").replace

        def fail_feed_replace(source, destination):
            if Path(destination) == self.feed_path:
                raise OSError("simulated finalization failure")
            return real_replace(source, destination)

        with patch("paper_feed.main.os.replace", side_effect=fail_feed_replace):
            with self.assertRaises(PipelineError):
                self.invoke_pipeline()
        self.assertEqual(self.feed_path.read_bytes(), before_feed)
        self.assertEqual(self.retry_path.read_bytes(), before_retries)

    def test_ready_duplicate_is_a_deterministic_no_op(self):
        self.invoke_pipeline()
        before_feed, before_retries = self.feed_path.read_bytes(), self.retry_path.read_bytes()
        result = self.invoke_pipeline()
        self.assertFalse(result.changed)
        self.assertEqual(self.feed_path.read_bytes(), before_feed)
        self.assertEqual(self.retry_path.read_bytes(), before_retries)

    def test_deterministic_order_prefers_alert_date_then_relevance_then_ingested_at_then_title(self):
        self.invoke_pipeline(messages=[(FIXTURES / "scholar_alert.html.eml").read_bytes()])
        titles = [paper["title"] for paper in json.loads(self.feed_path.read_text())["papers"]]
        self.assertEqual(titles, sorted(titles, key=str.casefold))

    def test_sort_order_uses_descending_ingested_time_before_title(self):
        summary = LocalizedSummary("Conclusion.", ("One.", "Two."), "Connection.", ("Tag",))

        def record(record_id, alert_date, relevance, ingested_at, title):
            return PaperRecord(record_id, title, ("Author",), "Venue", 2026, "https://example.invalid/paper", alert_date, ingested_at, "abstract", relevance, summary, summary, "ready")

        records = [
            record("doi:10.1000/old", "2026-09-09", "high", "2026-09-10T03:00:00Z", "Old"),
            record("doi:10.1000/transfer", "2026-09-10", "transferable", "2026-09-10T03:00:00Z", "Transfer"),
            record("doi:10.1000/early", "2026-09-10", "high", "2026-09-10T01:00:00Z", "A title"),
            record("doi:10.1000/late", "2026-09-10", "high", "2026-09-10T02:00:00Z", "Z title"),
        ]
        self.assertEqual([item.record_id for item in _sort_records(records)], [
            "doi:10.1000/late", "doi:10.1000/early", "doi:10.1000/transfer", "doi:10.1000/old",
        ])

    def test_distinct_candidate_urls_reconciled_to_same_enriched_doi_publish_one_card(self):
        messages = [
            self.alert_message("First alert", "https://one.example.invalid/paper"),
            self.alert_message("Second alert", "https://two.example.invalid/paper"),
        ]

        def same_doi(candidate):
            return PaperMetadata(candidate.title, candidate.authors, candidate.venue, candidate.year,
                                 candidate.canonical_url, "10.1000/shared", None,
                                 "Synthetic public abstract.", "abstract")

        result = self.invoke_pipeline(messages=messages, enricher=same_doi)
        payload = json.loads(self.feed_path.read_text())
        self.assertEqual(result.new, 1)
        self.assertEqual(result.summarized, 1)
        self.assertEqual(len(payload["papers"]), 1)
        self.assertEqual(payload["papers"][0]["record_id"], "doi:10.1000/shared")
        self.assertEqual(json.loads(self.retry_path.read_text())["retries"], {})

    def test_third_long_metadata_failure_is_bounded_fallback_without_blocking_other_paper(self):
        long_message = self.alert_message(
            "T" * 900, "https://long.example.invalid/paper", "A" * 700, "V" * 1400,
        )

        def fails_long(candidate):
            if candidate.title.startswith("T"):
                raise RuntimeError("private failure")
            return self.enricher(candidate)

        for _ in range(3):
            self.invoke_pipeline(messages=[long_message, self.messages[0]], enricher=fails_long)
        papers = json.loads(self.feed_path.read_text())["papers"]
        fallback = next(paper for paper in papers if paper["status"] == "summary_unavailable")
        self.assertLessEqual(len(fallback["title"]), 500)
        self.assertLessEqual(len(fallback["authors"][0]), 200)
        self.assertLessEqual(len(fallback["venue"]), 300)
        self.assertEqual(len([paper for paper in papers if paper["status"] == "ready"]), 1)

    def test_dry_run_preview_alias_never_overwrites_official_files(self):
        for preview_path in (self.feed_path, self.retry_path):
            with self.subTest(preview_path=preview_path.name):
                before_feed, before_retries = self.feed_path.read_bytes(), self.retry_path.read_bytes()
                with self.assertRaises(PipelineError):
                    self.invoke_pipeline(publish=False, preview_path=preview_path)
                self.assertEqual(self.feed_path.read_bytes(), before_feed)
                self.assertEqual(self.retry_path.read_bytes(), before_retries)

    def test_model_call_receives_three_public_research_strands_only(self):
        captured = {}
        response = {
            "relevance": "weak",
            "en": {"core_conclusion": "Conclusion.", "key_points": ["One.", "Two."], "research_connection": "Connection.", "tags": ["Tag"]},
            "zh": {"core_conclusion": "结论。", "key_points": ["一。", "二。"], "research_connection": "研究关联。", "tags": ["标签"]},
        }

        class Client:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def post(self, _url, **kwargs):
                captured.update(kwargs["json"])
                import httpx
                return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(response)}}]})

        metadata = self.enricher(type("Candidate", (), {"title": "Paper", "authors": ("Author",), "venue": "Venue", "year": 2026, "canonical_url": "https://example.invalid/paper"})())
        with patch("paper_feed.main.httpx.Client", return_value=Client()):
            _invoke_summarizer(summarize, metadata, self.settings)
        profile = json.loads(captured["messages"][1]["content"])["research_profile"].casefold()
        for phrase in ("brain dynamics", "neuroimaging", "complex systems", "contagion", "llm agents", "ai4science", "formal verification"):
            self.assertIn(phrase, profile)
        self.assertNotIn("recipient", json.dumps(captured))


if __name__ == "__main__":
    unittest.main()
