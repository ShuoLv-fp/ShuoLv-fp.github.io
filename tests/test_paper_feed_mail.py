from datetime import date
import os
from unittest import TestCase
from unittest.mock import patch


class FakeImap:
    def __init__(self):
        self.calls = []

    def login(self, username, secret):
        self.calls.append(("login", username, secret))
        return "OK", []

    def select(self, folder, readonly=False):
        self.calls.append(("select", folder, readonly))
        return "OK", [b"3"]

    def uid(self, command, *args):
        self.calls.append(("uid", command, *args))
        if command == "search":
            return "OK", [b"101 102"]
        return "OK", [(b"101 (BODY[] {10})", b"From: scholaralerts-noreply@google.com\nSubject: Scholar Alert - synthetic\nContent-Type: text/html\n\n<table><tr class='gse_alrt_title'><td><a href='https://example.invalid/paper'>Paper</a></td></tr></table>")]

    def logout(self):
        self.calls.append(("logout",))
        return "BYE", []


class SettingsTests(TestCase):
    def test_defaults_and_credentials_are_loaded_from_environment(self):
        from paper_feed.settings import Settings

        with patch.dict(os.environ, {
            "FOXMAIL_USERNAME": "reader@example.com",
            "FOXMAIL_IMAP_AUTH_CODE": "mail-secret",
            "DEEPSEEK_API_KEY": "model-secret",
        }, clear=True):
            settings = Settings.from_env(require_credentials=True)

        self.assertEqual(settings.imap_host, "imap.qq.com")
        self.assertEqual(settings.imap_port, 993)
        self.assertEqual(settings.imap_folder, "INBOX")
        self.assertEqual(settings.model, "deepseek-v4-flash-vision-exp")
        self.assertEqual(settings.deepseek_base_url, "https://api.deepseek.com")
        self.assertEqual(settings.allowed_senders, ("scholaralerts-noreply@google.com",))
        self.assertEqual(settings.subject_terms, ("Scholar Alert", "Google Scholar"))
        self.assertEqual(settings.recurring_lookback_days, 7)
        self.assertEqual(settings.first_run_lookback_days, 30)
        self.assertEqual(settings.timeout_seconds, 20)
        self.assertEqual(settings.model_attempts, 3)
        self.assertEqual(settings.foxmail_username, "reader@example.com")
        self.assertEqual(settings.foxmail_imap_auth_code, "mail-secret")

    def test_required_credentials_report_only_missing_variable_names(self):
        from paper_feed.settings import Settings, SettingsError

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SettingsError) as raised:
                Settings.from_env(require_credentials=True)

        message = str(raised.exception)
        self.assertIn("FOXMAIL_USERNAME", message)
        self.assertIn("FOXMAIL_IMAP_AUTH_CODE", message)
        self.assertIn("DEEPSEEK_API_KEY", message)
        self.assertNotIn("mail-secret", message)
        self.assertNotIn("model-secret", message)


class MailRetrievalTests(TestCase):
    def test_fetches_matching_alerts_without_mutating_messages(self):
        from paper_feed.mail import fetch_alert_messages
        from paper_feed.settings import Settings

        settings = Settings(
            foxmail_username="reader@example.com",
            foxmail_imap_auth_code="mail-secret",
            deepseek_api_key="model-secret",
        )
        client = FakeImap()
        with patch("paper_feed.mail.imaplib.IMAP4_SSL", return_value=client) as connect:
            messages = fetch_alert_messages(settings, date(2026, 9, 2))

        self.assertEqual(len(messages), 2)
        connect.assert_called_once_with("imap.qq.com", 993, timeout=20)
        self.assertIn(("login", "reader@example.com", "mail-secret"), client.calls)
        self.assertIn(("select", "INBOX", True), client.calls)
        self.assertIn(("uid", "search", None, "SINCE", "02-Sep-2026"), client.calls)
        self.assertEqual(
            [call for call in client.calls if call[:2] == ("uid", "fetch")],
            [("uid", "fetch", b"101", "(BODY.PEEK[])"), ("uid", "fetch", b"102", "(BODY.PEEK[])")],
        )
        self.assertIn(("logout",), client.calls)
        forbidden = ("BODY[]", "RFC822", "STORE", "\\\\Seen")
        self.assertFalse(any(
            any(token in str(value) for token in forbidden)
            for call in client.calls for value in call
        ))


if __name__ == "__main__":
    import unittest
    unittest.main()
