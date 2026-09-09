from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paper_feed.models import LocalizedSummary, PaperRecord, RetryEntry
from paper_feed.store import (
    merge_records,
    stable_record_id,
    validate_public_record,
    write_feed_atomic,
    write_retries_atomic,
)


class PaperFeedModelTests(unittest.TestCase):
    def sample(self) -> PaperRecord:
        return PaperRecord(
            record_id="doi:10.1000/example",
            title="A Public Paper",
            authors=("A. Author", "B. Author"),
            venue="Example Journal",
            year=2026,
            canonical_url="https://doi.org/10.1000/example",
            alert_date="2026-09-09",
            ingested_at="2026-09-09T01:00:00Z",
            evidence_type="abstract",
            relevance="high",
            en=LocalizedSummary(
                "Conclusion", ("Point one", "Point two"), "Connection", ("Brain",)
            ),
            zh=LocalizedSummary(
                "核心结论", ("要点一", "要点二"), "研究关联", ("脑科学",)
            ),
            status="ready",
        )

    def test_stable_id_prefers_doi(self):
        self.assertEqual(
            stable_record_id(
                "https://doi.org/10.1000/EXAMPLE", None, "https://x.test", "Title"
            ),
            "doi:10.1000/example",
        )

    def test_stable_id_strips_whitespace_before_normalizing_doi(self):
        self.assertEqual(
            stable_record_id("  https://doi.org/10.1000/EXAMPLE  ", None, None, "Title"),
            "doi:10.1000/example",
        )

    def test_stable_id_prefers_normalized_arxiv_identifier(self):
        self.assertEqual(
            stable_record_id(None, "  arXiv:2401.12345  ", "https://x.test", "Title"),
            "arxiv:2401.12345",
        )

    def test_stable_id_accepts_dotted_legacy_arxiv_categories(self):
        for source, expected in (
            (" math.GT/0309136 ", "arxiv:math.gt/0309136"),
            ("arXiv:cs.AI/0101010", "arxiv:cs.ai/0101010"),
        ):
            with self.subTest(source=source):
                self.assertEqual(stable_record_id(None, source, None, "Title"), expected)

    def test_stable_id_rejects_malformed_dotted_legacy_arxiv_identifier(self):
        self.assertRegex(
            stable_record_id(None, "math.GT/030913", None, "Title"),
            r"^title:[0-9a-f]{24}$",
        )

    def test_stable_id_uses_exact_hash_format_for_https_url_fallback(self):
        record_id = stable_record_id(None, None, "https://example.test/paper/", "Title")
        self.assertRegex(record_id, r"^url:[0-9a-f]{24}$")

    def test_stable_id_uses_title_hash_for_http_url(self):
        record_id = stable_record_id(None, None, "http://example.test/paper", "Title")
        self.assertRegex(record_id, r"^title:[0-9a-f]{24}$")

    def test_stable_id_title_fallback_has_exact_hash_format(self):
        self.assertRegex(
            stable_record_id(None, None, None, "A Public Paper"),
            r"^title:[0-9a-f]{24}$",
        )

    def test_stable_id_title_fallback_is_deterministic(self):
        self.assertEqual(
            stable_record_id(None, None, None, "  A   Public PAPER  "),
            stable_record_id(None, None, None, "a public paper"),
        )

    def test_merge_is_idempotent(self):
        record = self.sample()
        self.assertEqual(merge_records([record], [record]), [record])

    def test_forbidden_mailbox_field_is_rejected(self):
        payload = self.sample().to_public_dict()
        payload["message_id"] = "private"
        with self.assertRaisesRegex(ValueError, "forbidden public field"):
            validate_public_record(payload)

    def test_atomic_write_preserves_valid_envelope(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            write_feed_atomic(path, [self.sample()], "2026-09-09T01:00:00Z")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(len(payload["papers"]), 1)

    def test_failed_validation_preserves_old_bytes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            path.write_text('{"old": true}\n', encoding="utf-8")
            before = path.read_bytes()
            invalid = replace(self.sample(), canonical_url="http://127.0.0.1/private")
            with self.assertRaises(ValueError):
                write_feed_atomic(path, [invalid], "2026-09-09T01:00:00Z")
            self.assertEqual(path.read_bytes(), before)

    def test_metadata_only_fallback_accepts_the_minimal_unavailable_shape(self):
        fallback = replace(
            self.sample(),
            evidence_type="unavailable",
            status="summary_unavailable",
            en=LocalizedSummary("Summary temporarily unavailable", (), "", ()),
            zh=LocalizedSummary("摘要暂不可用", (), "", ()),
        )
        validate_public_record(fallback.to_public_dict())

    def test_ready_records_keep_required_localized_content(self):
        incomplete = replace(
            self.sample(),
            en=LocalizedSummary("Conclusion", (), "", ()),
        )
        with self.assertRaises(ValueError):
            validate_public_record(incomplete.to_public_dict())

    def test_public_record_allows_unknown_year(self):
        validate_public_record(replace(self.sample(), year=None).to_public_dict())

    def test_public_record_rejects_nonstable_and_private_record_ids(self):
        for record_id in (
            "arbitrary",
            "<mail@example.test>",
            "doi: message id",
            "doi:10.1000/ok\nnext",
            "arxiv:not-an-id",
            "arxiv:math.gt/030913",
        ):
            with self.subTest(record_id=record_id):
                with self.assertRaises(ValueError):
                    validate_public_record(replace(self.sample(), record_id=record_id).to_public_dict())

    def test_retry_state_rejects_invalid_record_id(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "retries.json"
            with self.assertRaises(ValueError):
                write_retries_atomic(
                    path,
                    {"recipient@example.test": RetryEntry(1, "2026-09-09", "timeout")},
                )

    def test_retry_state_rejects_unsanitized_error_category(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "retries.json"
            with self.assertRaises(ValueError):
                write_retries_atomic(
                    path,
                    {"doi:10.1000/example": RetryEntry(1, "2026-09-09", "raw alert body")},
                )


if __name__ == "__main__":
    unittest.main()
