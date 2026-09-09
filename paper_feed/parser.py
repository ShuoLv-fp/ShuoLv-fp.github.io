"""Parse Google Scholar alert messages into public paper candidates.

The parser deliberately consumes only the rendered MIME body.  Mailbox headers
and alert provenance are never copied into a :class:`PaperCandidate`.
"""

from __future__ import annotations

from datetime import timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
import re
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

from paper_feed.models import PaperCandidate


DEFAULT_SENDERS = ("scholaralerts-noreply@alerts.google.invalid",)
DEFAULT_SUBJECT_TERMS = ("Scholar Alert",)
MAX_RESULTS = 100


class ScholarParseError(ValueError):
    """A message looked like a Scholar alert but did not contain a usable result."""


def decode_google_target(url: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname.casefold() if parts.hostname else ""
    is_google_host = host == "google.com" or host.endswith(".google.com")
    has_credentials = parts.username is not None or parts.password is not None
    if parts.path.endswith("/scholar_url"):
        if not (parts.scheme == "https" and is_google_host and not has_credentials):
            return ""
        target = parse_qs(parts.query).get("url", [""])[0]
        return target if target.startswith("https://") else ""
    return url if parts.scheme == "https" and not has_credentials else ""


def clean_text(value: str, limit: int) -> str:
    return " ".join(value.split())[:limit].strip()


def _message(raw_message: bytes):
    return BytesParser(policy=policy.default).parsebytes(raw_message)


def _header_matches(message, allowed_senders: tuple[str, ...], subject_terms: tuple[str, ...]) -> bool:
    sender = parseaddr(message.get("From", ""))[1].casefold()
    allowed = {address.casefold() for address in allowed_senders}
    subject = str(message.get("Subject", ""))
    return sender in allowed and any(term.casefold() in subject.casefold() for term in subject_terms)


def is_scholar_alert(
    raw_message: bytes,
    allowed_senders: tuple[str, ...],
    subject_terms: tuple[str, ...],
) -> bool:
    """Return whether headers and MIME body identify a Scholar alert."""
    message = _message(raw_message)
    if not _header_matches(message, allowed_senders, subject_terms):
        return False
    html, plain = _message_bodies(message)
    return bool(_result_blocks(html, plain))


def parse_scholar_message(raw_message: bytes) -> list[PaperCandidate]:
    """Return public candidates from a valid Scholar alert, or none if unrelated."""
    message = _message(raw_message)
    if not _header_matches(message, DEFAULT_SENDERS, DEFAULT_SUBJECT_TERMS):
        return []
    html, plain = _message_bodies(message)
    blocks = _result_blocks(html, plain)
    if not blocks:
        return []
    alert_date = _alert_date(str(message.get("Date", "")))
    candidates = []
    malformed = False
    for title, url, bibliographic, snippet in blocks[:MAX_RESULTS]:
        canonical_url = decode_google_target(url)
        if not title or not canonical_url:
            malformed = True
            continue
        authors, venue, year = _bibliographic_fields(bibliographic)
        candidates.append(
            PaperCandidate(
                title=clean_text(title, 500),
                authors=authors,
                venue=venue,
                year=year,
                canonical_url=canonical_url,
                alert_date=alert_date,
                snippet=clean_text(snippet, 4000),
            )
        )
    if malformed:
        raise ScholarParseError("recognized Scholar alert contains a malformed result")
    return candidates


def _message_bodies(message) -> tuple[str, str]:
    html_parts: list[str] = []
    plain_parts: list[str] = []
    for part in message.walk():
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/html", "text/plain"}:
            continue
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        (html_parts if content_type == "text/html" else plain_parts).append(text)
    return "\n".join(html_parts), "\n".join(plain_parts)


def _result_blocks(html: str, plain: str) -> list[tuple[str, str, str, str]]:
    """Prefer Scholar's HTML cards, with plain text as a usable fallback."""
    return _html_blocks(html) or _plain_blocks(plain)


def _html_blocks(html: str) -> list[tuple[str, str, str, str]]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script, style, form"):
        node.decompose()
    for node in soup.find_all(["img", "div", "table", "p", "span"]):
        if node.parent is None:
            continue
        classes = " ".join(node.get("class", []))
        marker = f"{classes} {node.get('id', '')} {node.get_text(' ', strip=True)}".casefold()
        has_result_card = node.select_one(".gse_alrt_title") is not None
        if not has_result_card and ("footer" in marker or "unsubscribe" in marker or (
            node.name == "img" and (node.get("width") == "1" or node.get("height") == "1")
        )):
            node.decompose()
    results = []
    for title_node in soup.select(".gse_alrt_title")[:MAX_RESULTS]:
        container = title_node.find_parent(class_=lambda value: value and "gse_alrt" in value)
        container = container or title_node.parent
        link = title_node.find("a", href=True)
        results.append((
            clean_text(title_node.get_text(" ", strip=True), 500),
            link["href"] if link else "",
            _class_text(container, "gse_alrt_meta", 1000),
            _class_text(container, "gse_alrt_snippet", 4000),
        ))
    return results


def _class_text(container: Tag | None, class_name: str, limit: int) -> str:
    node = container.find(class_=class_name) if container else None
    return clean_text(node.get_text(" ", strip=True), limit) if node else ""


def _plain_blocks(plain: str) -> list[tuple[str, str, str, str]]:
    if "google scholar" not in plain.casefold():
        return []
    lines = [clean_text(line, 4000) for line in plain.splitlines()]
    results = []
    for index, line in enumerate(lines):
        if not line.startswith("https://") or index == 0:
            continue
        title = lines[index - 1]
        bibliographic = lines[index + 1] if index + 1 < len(lines) else ""
        snippet = lines[index + 2] if index + 2 < len(lines) else ""
        if title and bibliographic and snippet and "unsubscribe" not in title.casefold():
            results.append((title, line, bibliographic, snippet))
    return results


def _bibliographic_fields(value: str) -> tuple[tuple[str, ...], str, int | None]:
    value = clean_text(value, 1000)
    authors_text, separator, publication = value.partition(" - ")
    authors = tuple(clean_text(author, 500) for author in authors_text.split(",") if clean_text(author, 500))
    year_match = re.search(r"\b(?:19|20)\d{2}\b", publication or value)
    year = int(year_match.group()) if year_match else None
    venue = publication
    if year_match:
        venue = publication[:year_match.start()].rstrip(" ,-")
    return authors, clean_text(venue, 1000), year


def _alert_date(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return ""
    if parsed is None:
        return ""
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.date().isoformat()
