from pathlib import Path
import unittest

from paper_feed.parser import (
    DEFAULT_SENDERS,
    ScholarParseError,
    _plain_blocks,
    decode_google_target,
    is_scholar_alert,
    parse_scholar_message,
)


FIXTURES = Path("tests/fixtures")


class ScholarParserTests(unittest.TestCase):
    def test_html_alert_yields_only_paper_fields(self):
        raw = (FIXTURES / "scholar_alert.html.eml").read_bytes()
        self.assertTrue(is_scholar_alert(raw, ("scholaralerts-noreply@alerts.google.invalid",), ("Scholar Alert",)))
        papers = parse_scholar_message(raw)
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0].title, "Foundation Models for Brain Dynamics")
        self.assertEqual(papers[0].canonical_url, "https://example.invalid/paper-one")
        self.assertFalse(hasattr(papers[0], "message_id"))
        self.assertFalse(hasattr(papers[0], "trigger_author"))

    def test_production_filter_accepts_the_real_scholar_sender(self):
        raw = b"""From: scholaralerts-noreply@google.com
Subject: Scholar Alert - synthetic result
Content-Type: text/html; charset=UTF-8

<table><tr class="gse_alrt_title"><td><a href="https://example.invalid/paper">Selected result</a></td></tr></table>
"""
        self.assertTrue(is_scholar_alert(raw, ("scholaralerts-noreply@google.com",), ("Scholar Alert",)))
        self.assertEqual(
            DEFAULT_SENDERS,
            (
                "scholaralerts-noreply@google.com",
                "scholarcitations-noreply@google.com",
            ),
        )
        self.assertEqual(len(parse_scholar_message(raw)), 1)

    def test_production_filter_accepts_followed_author_notifications(self):
        raw = b"""From: Google Scholar Citations <scholarcitations-noreply@google.com>
Subject: Follow articles by Example Researcher
Content-Type: text/html

<table class="gse_alrt"><tr><td class="gse_alrt_title"><a href="https://example.invalid/paper">A public paper</a></td></tr></table>
"""
        self.assertTrue(
            is_scholar_alert(raw, DEFAULT_SENDERS, ("Follow articles by",))
        )

    def test_fixture_filtering_and_parsing_use_separate_responsibilities(self):
        raw = (FIXTURES / "scholar_alert.html.eml").read_bytes()
        self.assertTrue(is_scholar_alert(raw, ("scholaralerts-noreply@alerts.google.invalid",), ("Scholar Alert",)))
        self.assertEqual(len(parse_scholar_message(raw)), 2)

    def test_unrelated_email_is_rejected(self):
        raw = b"From: newsletter@example.invalid\nSubject: Weekly news\n\nHello"
        self.assertFalse(is_scholar_alert(raw, ("scholaralerts-noreply@alerts.google.invalid",), ("Scholar Alert",)))

    def test_plain_text_alert_is_supported(self):
        papers = parse_scholar_message((FIXTURES / "scholar_alert.txt.eml").read_bytes())
        self.assertEqual(len(papers), 1)
        self.assertTrue(papers[0].canonical_url.startswith("https://"))

    def test_alert_date_uses_asia_shanghai_calendar_day(self):
        raw = b"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - synthetic result
Date: Wed, 09 Sep 2026 00:30:00 +0800
Content-Type: text/plain; charset=UTF-8

Google Scholar
Timezone Boundary Paper
https://example.invalid/timezone-paper
Taylor Synthetic - Imaginary Journal, 2026
Synthetic public evidence.
"""
        self.assertEqual(parse_scholar_message(raw)[0].alert_date, "2026-09-09")

    def test_plain_text_is_used_when_html_has_no_results(self):
        raw = b"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - synthetic result
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary=part

--part
Content-Type: text/plain; charset=UTF-8

Google Scholar
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
        raw = b"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - synthetic result
Content-Type: text/html; charset=UTF-8

<table><tr class="gse_alrt_title"><td><a href="http://example.invalid/not-secure">Broken result</a></td></tr></table>
"""
        with self.assertRaises(ScholarParseError):
            parse_scholar_message(raw)

    def test_footer_child_does_not_remove_its_valid_result_wrapper(self):
        papers = parse_scholar_message((FIXTURES / "scholar_alert_footer_wrapper.eml").read_bytes())
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].title, "Result Survives Nested Footer")

    def test_google_redirect_requires_exact_google_host_or_subdomain(self):
        target = "https%3A%2F%2Fexample.invalid%2Fpaper"
        self.assertEqual(
            decode_google_target(f"https://google.com/scholar_url?url={target}"),
            "https://example.invalid/paper",
        )
        self.assertEqual(
            decode_google_target(f"https://scholar.google.com/scholar_url?url={target}"),
            "https://example.invalid/paper",
        )
        for deceptive_url in (
            f"https://notgoogle.com/scholar_url?url={target}",
            f"https://google.com.evil.invalid/scholar_url?url={target}",
            f"https://google.com@evil.invalid/scholar_url?url={target}",
            f"https://google.com:invalid/scholar_url?url={target}",
            "https://google.com/scholar_url?url=http%3A%2F%2Fexample.invalid%2Fpaper",
            "https://google.com/scholar_url?url=https%3A%2F%2Fuser%3Asecret%40example.invalid%2Fpaper",
        ):
            self.assertEqual(decode_google_target(deceptive_url), "")

    def test_malformed_url_in_recognized_result_raises_typed_error(self):
        raw = b"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - synthetic result
Content-Type: text/html; charset=UTF-8

<table><tr class="gse_alrt_title"><td><a href="https://scholar.google.com/scholar_url?url=https%3A%2F%2F%5Bbad">Broken URL</a></td></tr></table>
"""
        with self.assertRaises(ScholarParseError):
            parse_scholar_message(raw)

    def test_plain_text_shape_without_scholar_marker_is_rejected(self):
        raw = b"""From: scholaralerts-noreply@alerts.google.invalid
Subject: Scholar Alert - unrelated synthetic mail
Content-Type: text/plain; charset=UTF-8

Unrelated Four Line Message
https://example.invalid/unrelated
Taylor Synthetic - Imaginary Journal, 2026
This shape alone must not be parsed as a Scholar alert.
"""
        self.assertEqual(parse_scholar_message(raw), [])

    def test_plain_text_extractor_stops_after_one_hundred_results(self):
        result = "\n".join(
            (
                f"Synthetic Result {index}\n"
                f"https://example.invalid/result-{index}\n"
                f"Author {index} - Synthetic Venue, 2026\n"
                f"Synthetic snippet {index}."
            )
            for index in range(101)
        )
        body = f"Google Scholar\n{result}"
        raw = (
            "From: scholaralerts-noreply@alerts.google.invalid\n"
            "Subject: Scholar Alert - synthetic bulk result\n"
            "Content-Type: text/plain; charset=UTF-8\n\n"
            f"{body}"
        ).encode()
        self.assertEqual(len(_plain_blocks(body)), 100)
        self.assertEqual(len(parse_scholar_message(raw)), 100)


if __name__ == "__main__":
    unittest.main()
