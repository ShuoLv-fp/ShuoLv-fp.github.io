"""Validation, deterministic merging, and atomic persistence for public feed data."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Mapping, Optional, Union
from urllib.parse import urlsplit, urlunsplit

from .models import LocalizedSummary, PaperRecord, RetryEntry


SCHEMA_VERSION = 1
TIMEZONE = "Asia/Shanghai"
RELEVANCE_ORDER = {"high": 0, "transferable": 1, "weak": 2}
FORBIDDEN_KEYS = {
    "message_id",
    "sender",
    "recipient",
    "mailbox",
    "raw_email",
    "subscription_author",
    "trigger_author",
    "imap_uid",
    "snippet_raw",
}
PUBLIC_RECORD_KEYS = {
    "record_id",
    "title",
    "authors",
    "venue",
    "year",
    "canonical_url",
    "alert_date",
    "ingested_at",
    "evidence_type",
    "relevance",
    "en",
    "zh",
    "status",
}
LOCALIZED_SUMMARY_KEYS = {
    "core_conclusion",
    "key_points",
    "research_connection",
    "tags",
}
MAX_LENGTHS = {
    "record_id": 300,
    "title": 500,
    "author": 200,
    "venue": 300,
    "core_conclusion": 1500,
    "key_point": 600,
    "research_connection": 1000,
    "tag": 100,
    "error_category": 100,
}
SAFE_ERROR_CATEGORIES = {
    "timeout",
    "network_error",
    "metadata_error",
    "summary_error",
    "rate_limited",
    "server_error",
    "malformed_response",
    "schema_error",
    "no_evidence",
    "unknown_error",
}
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+$")
ARXIV_PATTERN = re.compile(
    r"(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+(?:\.[a-z-]+)*/\d{7}(?:v\d+)?)$"
)
HASH_RECORD_ID_PATTERN = re.compile(r"[0-9a-f]{24}$")
UNAVAILABLE_CONCLUSIONS = {
    "en": "Summary temporarily unavailable",
    "zh": "摘要暂不可用",
}


def stable_record_id(
    doi: Optional[str], arxiv_id: Optional[str], canonical_url: Optional[str], title: str
) -> str:
    if doi:
        value = doi.strip().lower().removeprefix("https://doi.org/").removeprefix("doi:").strip()
        if DOI_PATTERN.fullmatch(value):
            return f"doi:{value}"
    if arxiv_id:
        value = arxiv_id.strip().lower().removeprefix("arxiv:").strip()
        if ARXIV_PATTERN.fullmatch(value):
            return f"arxiv:{value}"
    if canonical_url:
        try:
            _validate_public_url(canonical_url.strip())
        except ValueError:
            pass
        else:
            parts = urlsplit(canonical_url.strip())
            canonical = urlunsplit(
                (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, "")
            )
            return "url:" + hashlib.sha256(canonical.encode()).hexdigest()[:24]
    normalized = " ".join(title.casefold().split())
    return "title:" + hashlib.sha256(normalized.encode()).hexdigest()[:24]


def _non_empty_string(value: Any, field: str, limit: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"invalid {field}")


def _validate_date(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"invalid {field}")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"invalid {field}") from error


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("invalid ingested_at")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("invalid ingested_at") from error


def _validate_public_url(value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError("invalid canonical_url")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("invalid canonical_url")
    try:
        address = ipaddress.ip_address(parts.hostname)
    except ValueError:
        if parts.hostname.lower() == "localhost":
            raise ValueError("invalid canonical_url")
    else:
        if not address.is_global:
            raise ValueError("invalid canonical_url")


def _validate_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden public field: {key}")
            _validate_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _validate_no_forbidden_keys(nested)


def _validate_localized_summary(value: Any, language: str, ready: bool) -> None:
    if not isinstance(value, Mapping) or set(value) != LOCALIZED_SUMMARY_KEYS:
        raise ValueError(f"invalid {language} summary schema")
    key_points = value["key_points"]
    tags = value["tags"]
    if ready:
        _non_empty_string(
            value["core_conclusion"], f"{language}.core_conclusion", MAX_LENGTHS["core_conclusion"]
        )
        _non_empty_string(
            value["research_connection"],
            f"{language}.research_connection",
            MAX_LENGTHS["research_connection"],
        )
        if not isinstance(key_points, list) or len(key_points) not in (2, 3):
            raise ValueError(f"invalid {language}.key_points")
        if not isinstance(tags, list) or not 1 <= len(tags) <= 5:
            raise ValueError(f"invalid {language}.tags")
    else:
        if value["core_conclusion"] != UNAVAILABLE_CONCLUSIONS[language]:
            raise ValueError(f"invalid {language}.core_conclusion")
        if not isinstance(value["research_connection"], str) or len(value["research_connection"]) > MAX_LENGTHS["research_connection"]:
            raise ValueError(f"invalid {language}.research_connection")
        if not isinstance(key_points, list) or len(key_points) > 3:
            raise ValueError(f"invalid {language}.key_points")
        if not isinstance(tags, list) or len(tags) > 5:
            raise ValueError(f"invalid {language}.tags")
    if not isinstance(key_points, list):
        raise ValueError(f"invalid {language}.key_points")
    for point in key_points:
        _non_empty_string(point, f"{language}.key_point", MAX_LENGTHS["key_point"])
    if not isinstance(tags, list):
        raise ValueError(f"invalid {language}.tags")
    for tag in tags:
        _non_empty_string(tag, f"{language}.tag", MAX_LENGTHS["tag"])


def validate_public_record(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public record must be an object")
    _validate_no_forbidden_keys(payload)
    if set(payload) != PUBLIC_RECORD_KEYS:
        raise ValueError("invalid public record schema")
    _validate_stable_record_id(payload["record_id"])
    _non_empty_string(payload["title"], "title", MAX_LENGTHS["title"])
    authors = payload["authors"]
    if not isinstance(authors, list):
        raise ValueError("invalid authors")
    for author in authors:
        _non_empty_string(author, "author", MAX_LENGTHS["author"])
    if not isinstance(payload["venue"], str) or len(payload["venue"]) > MAX_LENGTHS["venue"]:
        raise ValueError("invalid venue")
    if payload["year"] is not None and (
        not isinstance(payload["year"], int) or not 1000 <= payload["year"] <= 9999
    ):
        raise ValueError("invalid year")
    _validate_public_url(payload["canonical_url"])
    _validate_date(payload["alert_date"], "alert_date")
    _validate_timestamp(payload["ingested_at"])
    if payload["evidence_type"] not in {"abstract", "snippet", "metadata", "unavailable"}:
        raise ValueError("invalid evidence_type")
    if payload["relevance"] not in RELEVANCE_ORDER:
        raise ValueError("invalid relevance")
    if payload["status"] not in {"ready", "summary_unavailable"}:
        raise ValueError("invalid status")
    ready = payload["status"] == "ready"
    _validate_localized_summary(payload["en"], "en", ready)
    _validate_localized_summary(payload["zh"], "zh", ready)


def _record_from_public_dict(payload: Mapping[str, Any]) -> PaperRecord:
    validate_public_record(payload)
    return PaperRecord(
        record_id=payload["record_id"],
        title=payload["title"],
        authors=tuple(payload["authors"]),
        venue=payload["venue"],
        year=payload["year"],
        canonical_url=payload["canonical_url"],
        alert_date=payload["alert_date"],
        ingested_at=payload["ingested_at"],
        evidence_type=payload["evidence_type"],
        relevance=payload["relevance"],
        en=LocalizedSummary(
            payload["en"]["core_conclusion"],
            tuple(payload["en"]["key_points"]),
            payload["en"]["research_connection"],
            tuple(payload["en"]["tags"]),
        ),
        zh=LocalizedSummary(
            payload["zh"]["core_conclusion"],
            tuple(payload["zh"]["key_points"]),
            payload["zh"]["research_connection"],
            tuple(payload["zh"]["tags"]),
        ),
        status=payload["status"],
    )


def _validate_feed_envelope(payload: Any) -> None:
    if not isinstance(payload, Mapping) or set(payload) != {
        "schema_version", "generated_at", "timezone", "papers"
    }:
        raise ValueError("invalid feed envelope")
    if payload["schema_version"] != SCHEMA_VERSION or payload["timezone"] != TIMEZONE:
        raise ValueError("unsupported feed envelope")
    if payload["generated_at"] is not None:
        _validate_timestamp(payload["generated_at"])
    if not isinstance(payload["papers"], list):
        raise ValueError("invalid feed papers")
    for record in payload["papers"]:
        validate_public_record(record)


def load_feed(path: Union[Path, str]) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_feed_envelope(payload)
    return payload


def merge_records(
    existing: Iterable[PaperRecord], incoming: Iterable[PaperRecord]
) -> list[PaperRecord]:
    merged: dict[str, PaperRecord] = {}
    for record in existing:
        validate_public_record(record.to_public_dict())
        merged.setdefault(record.record_id, record)
    for record in incoming:
        validate_public_record(record.to_public_dict())
        merged.setdefault(record.record_id, record)
    return sorted(
        merged.values(),
        key=lambda record: (RELEVANCE_ORDER[record.relevance], record.alert_date, record.record_id),
    )


def _write_json_atomic(path: Union[Path, str], payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as temporary:
            temporary_name = temporary.name
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        Path(temporary_name).replace(destination)
    except Exception:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def write_feed_atomic(
    path: Union[Path, str], records: Iterable[PaperRecord], generated_at: Optional[str]
) -> None:
    if generated_at is not None:
        _validate_timestamp(generated_at)
    papers = [record.to_public_dict() for record in records]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "timezone": TIMEZONE,
        "papers": papers,
    }
    _validate_feed_envelope(payload)
    _write_json_atomic(path, payload)


def _validate_stable_record_id(value: Any) -> None:
    _non_empty_string(value, "record_id", MAX_LENGTHS["record_id"])
    if value.startswith("doi:"):
        valid = DOI_PATTERN.fullmatch(value[4:])
    elif value.startswith("arxiv:"):
        valid = ARXIV_PATTERN.fullmatch(value[6:])
    elif value.startswith(("url:", "title:")):
        valid = HASH_RECORD_ID_PATTERN.fullmatch(value.split(":", 1)[1])
    else:
        valid = None
    if valid is None:
        raise ValueError("invalid retry record_id")


def _validate_retry_entry(value: Any) -> RetryEntry:
    if not isinstance(value, Mapping) or set(value) != {
        "attempts", "last_attempt_date", "error_category"
    }:
        raise ValueError("invalid retry entry")
    if not isinstance(value["attempts"], int) or value["attempts"] < 0:
        raise ValueError("invalid retry attempts")
    _validate_date(value["last_attempt_date"], "last_attempt_date")
    if value["error_category"] not in SAFE_ERROR_CATEGORIES:
        raise ValueError("invalid error_category")
    return RetryEntry(value["attempts"], value["last_attempt_date"], value["error_category"])


def load_retries(path: Union[Path, str]) -> dict[str, RetryEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or set(payload) != {"schema_version", "retries"}:
        raise ValueError("invalid retries envelope")
    if payload["schema_version"] != SCHEMA_VERSION or not isinstance(payload["retries"], Mapping):
        raise ValueError("unsupported retries envelope")
    entries: dict[str, RetryEntry] = {}
    for record_id, entry in payload["retries"].items():
        _validate_stable_record_id(record_id)
        entries[record_id] = _validate_retry_entry(entry)
    return entries


def write_retries_atomic(path: Union[Path, str], entries: Mapping[str, RetryEntry]) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "retries": {record_id: entry.to_dict() for record_id, entry in entries.items()},
    }
    loadable_entries = payload["retries"]
    for record_id, entry in loadable_entries.items():
        _validate_stable_record_id(record_id)
        _validate_retry_entry(entry)
    _write_json_atomic(path, payload)
