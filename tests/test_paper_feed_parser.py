from pathlib import Path
import unittest

from paper_feed.parser import ScholarParseError, is_scholar_alert, parse_scholar_message


FIXTURES = Path("tests/fixtures")


class ScholarParserTests(unittest.TestCase):
    def test_html_alert_yields_only_paper_fields(self):
        raw = (FIXTURES / "scholar_alert.html.eml").read_bytes()
        self.assertTrue(is_scholar_alert(raw, ("scholaralerts-noreply@google.com",), ("Scholar Alert",)))
        papers = parse_scholar_message(raw)
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0].title, "Foundation Models for Brain Dynamics")
        self.assertEqual(papers[0].canonical_url, "https://example.invalid/paper-one")
        self.assertFalse(hasattr(papers[0], "message_id"))
        self.assertFalse(hasattr(papers[0], "trigger_author"))

    def test_unrelated_email_is_rejected(self):
        raw = b"From: newsletter@example.invalid\nSubject: Weekly news\n\nHello"
        self.assertFalse(is_scholar_alert(raw, ("scholaralerts-noreply@google.com",), ("Scholar Alert",)))

    def test_plain_text_alert_is_supported(self):
        papers = parse_scholar_message((FIXTURES / "scholar_alert.txt.eml").read_bytes())
        self.assertEqual(len(papers), 1)
        self.assertTrue(papers[0].canonical_url.startswith("https://"))

    def test_plain_text_is_used_when_html_has_no_results(self):
        raw = b"""From: scholaralerts-noreply@google.com
Subject: Scholar Alert - synthetic result
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary=part

--part
Content-Type: text/plain; charset=UTF-8

Fallback Paper
https://example.invalid/fallback-paper
Taylor Synthetic - Imaginary Journal, 2026
An invented fallback result.
--part
Content-Type: text/html; charset=UTF-8

<html><body><p>No result cards here.</p></body></html>
--part--
"""
        papers = parse_scholar_message(raw)
        self.assertEqual(papers[0].canonical_url, "https://example.invalid/fallback-paper")

    def test_recognized_alert_with_a_malformed_result_raises_typed_error(self):
        raw = b"""From: scholaralerts-noreply@google.com
Subject: Scholar Alert - synthetic result
Content-Type: text/html; charset=UTF-8

<table><tr class="gse_alrt_title"><td><a href="http://example.invalid/not-secure">Broken result</a></td></tr></table>
"""
        with self.assertRaises(ScholarParseError):
            parse_scholar_message(raw)


if __name__ == "__main__":
    unittest.main()
