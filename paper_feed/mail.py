"""Read Google Scholar alerts from Foxmail without changing mailbox state."""

from __future__ import annotations

from datetime import date
import imaplib
import logging

from paper_feed.parser import is_scholar_alert
from paper_feed.settings import Settings


LOGGER = logging.getLogger(__name__)


class MailError(RuntimeError):
    """A mailbox operation could not complete safely."""


def fetch_alert_messages(settings: Settings, since: date) -> list[bytes]:
    """Retrieve matching alert message bodies, leaving all mailbox flags unchanged."""
    try:
        client = imaplib.IMAP4_SSL(
            settings.imap_host, settings.imap_port, timeout=settings.timeout_seconds
        )
    except Exception:
        raise MailError("unable to connect to configured mailbox") from None

    fetched_count = 0
    matched: list[bytes] = []
    try:
        try:
            client.login(settings.foxmail_username, settings.foxmail_imap_auth_code)
            status, _ = client.select(settings.imap_folder, readonly=True)
            if status != "OK":
                raise MailError("unable to select configured mailbox")
            status, data = client.uid("search", None, "SINCE", since.strftime("%d-%b-%Y"))
            if status != "OK":
                raise MailError("IMAP search failed")
            for uid in data[0].split():
                status, parts = client.uid("fetch", uid, "(BODY.PEEK[])")
                if status != "OK":
                    raise MailError("IMAP fetch failed")
                raw_message = next(part[1] for part in parts if isinstance(part, tuple))
                fetched_count += 1
                if is_scholar_alert(raw_message, settings.allowed_senders, settings.subject_terms):
                    matched.append(raw_message)
        except MailError:
            raise
        except Exception:
            raise MailError("mailbox retrieval failed") from None
        LOGGER.info("fetched=%d matched=%d", fetched_count, len(matched))
        return matched
    finally:
        try:
            client.logout()
        except Exception:
            pass
