"""Safe, injectable orchestration for the public paper feed."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

import httpx

from paper_feed.mail import fetch_alert_messages
from paper_feed.metadata import enrich_candidate, metadata_from_candidate
from paper_feed.models import LocalizedSummary, PaperCandidate, PaperMetadata, PaperRecord, PaperSummary, RetryEntry
from paper_feed.parser import ScholarParseError, parse_scholar_message
from paper_feed.settings import Settings
from paper_feed.store import (
    SAFE_ERROR_CATEGORIES,
    SCHEMA_VERSION,
    TIMEZONE,
    MAX_LENGTHS,
    load_feed,
    load_retries,
    stable_record_id,
    validate_public_record,
    write_feed_atomic,
    write_retries_atomic,
)
from paper_feed.summarizer import summarize


PUBLIC_RESEARCH_PROFILE = (
    "Public research spans human brain dynamics, neuroimaging, and AI; complex systems, "
    "network and contagion dynamics; and LLM agents for AI4Science and formal verification."
)


class PipelineError(RuntimeError):
    """A pipeline-wide error prevented publication."""


@dataclass(frozen=True)
class RunSummary:
    matched_alerts: int = 0
    candidates: int = 0
    duplicates: int = 0
    new: int = 0
    summarized: int = 0
    deferred: int = 0
    metadata_only: int = 0
    changed: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "matched_alerts": self.matched_alerts,
            "candidates": self.candidates,
            "duplicates": self.duplicates,
            "new": self.new,
            "summarized": self.summarized,
            "deferred": self.deferred,
            "metadata_only": self.metadata_only,
            "changed": self.changed,
        }


def _timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sort_records(records: list[PaperRecord]) -> list[PaperRecord]:
    order = {"high": 0, "transferable": 1, "weak": 2}
    ordered = sorted(records, key=lambda record: (record.title.casefold(), record.record_id))
    ordered.sort(key=lambda record: record.ingested_at, reverse=True)
    ordered.sort(key=lambda record: order[record.relevance])
    ordered.sort(key=lambda record: record.alert_date, reverse=True)
    return ordered


def _error_category(error: Exception, fallback: str) -> str:
    value = str(error)
    return value if value in SAFE_ERROR_CATEGORIES else fallback


def _fallback_record(candidate: PaperCandidate, record_id: str, timestamp: str) -> PaperRecord:
    def clean(value: object, limit: int, fallback: str) -> str:
        return " ".join(str(value or "").split())[:limit].strip() or fallback

    authors = tuple(clean(author, MAX_LENGTHS["author"], "Unknown author") for author in candidate.authors if str(author).strip())
    return PaperRecord(
        record_id=record_id,
        title=clean(candidate.title, MAX_LENGTHS["title"], "Untitled paper"), authors=authors or ("Unknown author",),
        venue=clean(candidate.venue, MAX_LENGTHS["venue"], "Unavailable venue"), year=candidate.year,
        canonical_url=candidate.canonical_url.strip(), alert_date=candidate.alert_date,
        ingested_at=timestamp, evidence_type="unavailable", relevance="weak",
        en=LocalizedSummary("Summary temporarily unavailable", (), "", ()),
        zh=LocalizedSummary("摘要暂不可用", (), "", ()), status="summary_unavailable",
    )


def _ready_record(metadata: PaperMetadata, candidate: PaperCandidate, summary: PaperSummary, record_id: str, timestamp: str) -> PaperRecord:
    return PaperRecord(
        record_id=record_id, title=metadata.title, authors=metadata.authors,
        venue=metadata.venue or candidate.venue or "Unavailable venue", year=metadata.year,
        canonical_url=metadata.canonical_url, alert_date=candidate.alert_date,
        ingested_at=timestamp, evidence_type=metadata.evidence_type, relevance=summary.relevance,
        en=summary.en, zh=summary.zh, status="ready",
    )


def _invoke_enricher(enricher, candidate: PaperCandidate) -> PaperMetadata:
    if enricher is enrich_candidate:
        with httpx.Client() as client:
            return enricher(candidate, client)
    return enricher(candidate)


def _invoke_summarizer(summarizer, metadata: PaperMetadata, settings: Settings) -> PaperSummary:
    if summarizer is summarize:
        with httpx.Client() as client:
            return summarizer(metadata, PUBLIC_RESEARCH_PROFILE, settings, client)
    return summarizer(metadata)


def _feed_payload(records: list[PaperRecord], timestamp: str) -> dict:
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": timestamp, "timezone": TIMEZONE,
               "papers": [record.to_public_dict() for record in records]}
    for paper in payload["papers"]:
        validate_public_record(paper)
    return payload


def _paths_alias(left: Path, right: Path) -> bool:
    left, right = Path(left), Path(right)
    if left.resolve() == right.resolve():
        return True
    try:
        return left.samefile(right)
    except OSError:
        return False


def _stage_and_publish(feed_path: Path, retry_path: Path, records: list[PaperRecord], retries: dict[str, RetryEntry], timestamp: str) -> None:
    """Validate both staged files, then replace together or restore exact prior bytes."""
    feed_path, retry_path = Path(feed_path), Path(retry_path)
    feed_before = feed_path.read_bytes() if feed_path.exists() else None
    retry_before = retry_path.read_bytes() if retry_path.exists() else None
    staged: list[Path] = []
    try:
        for path, writer, args in (
            (retry_path, write_retries_atomic, (retries,)),
            (feed_path, write_feed_atomic, (records, timestamp)),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            handle, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            os.close(handle)
            temporary = Path(name)
            temporary.unlink()
            writer(temporary, *args)
            staged.append(temporary)
        load_retries(staged[0])
        load_feed(staged[1])
        os.replace(staged[0], retry_path)
        os.replace(staged[1], feed_path)
    except Exception as error:
        # Both originals are retained as bytes so a partial finalization is reversible.
        for path, original in ((feed_path, feed_before), (retry_path, retry_before)):
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        raise PipelineError("publication failed") from error
    finally:
        for temporary in staged:
            temporary.unlink(missing_ok=True)


def run_pipeline(
    settings: Settings, raw_messages: list[bytes], feed_path: Path, retry_path: Path,
    publish: bool, now: datetime, preview_path: Path | None = None,
    enricher: Callable = enrich_candidate, summarizer: Callable = summarize,
) -> RunSummary:
    """Parse all alerts first, isolate per-paper errors, and publish only valid state."""
    if preview_path is not None and (
        _paths_alias(preview_path, feed_path) or _paths_alias(preview_path, retry_path)
    ):
        raise PipelineError("preview path conflicts with official state")
    try:
        existing_payload = load_feed(feed_path)
        retries = load_retries(retry_path)
        candidates: list[PaperCandidate] = []
        for message in raw_messages:
            candidates.extend(parse_scholar_message(message))
    except (OSError, ValueError, json.JSONDecodeError, ScholarParseError) as error:
        raise PipelineError("input validation failed") from error

    unique: dict[str, PaperCandidate] = {}
    for candidate in candidates:
        identifier = stable_record_id(candidate.doi, candidate.arxiv_id, candidate.canonical_url, candidate.title)
        unique.setdefault(identifier, candidate)
    original_retries = dict(retries)
    records = [
        PaperRecord(
            record_id=paper["record_id"], title=paper["title"], authors=tuple(paper["authors"]), venue=paper["venue"],
            year=paper["year"], canonical_url=paper["canonical_url"], alert_date=paper["alert_date"],
            ingested_at=paper["ingested_at"], evidence_type=paper["evidence_type"], relevance=paper["relevance"],
            en=LocalizedSummary(paper["en"]["core_conclusion"], tuple(paper["en"]["key_points"]), paper["en"]["research_connection"], tuple(paper["en"]["tags"])),
            zh=LocalizedSummary(paper["zh"]["core_conclusion"], tuple(paper["zh"]["key_points"]), paper["zh"]["research_connection"], tuple(paper["zh"]["tags"])), status=paper["status"],
        ) for paper in existing_payload["papers"]
    ]
    by_id = {record.record_id: record for record in records}
    existing_aliases: dict[str, str] = {}
    for record in sorted(records, key=lambda item: item.record_id):
        if record.status != "ready" or not record.record_id.startswith(("doi:", "arxiv:")):
            continue
        for alias in (
            stable_record_id(None, None, record.canonical_url, record.title),
            stable_record_id(None, None, None, record.title),
        ):
            existing_aliases.setdefault(alias, record.record_id)
    timestamp, today = _timestamp(now), now.astimezone(timezone.utc).date().isoformat()
    summarized = deferred = metadata_only = new = 0
    resolved: dict[str, tuple[str, PaperCandidate, PaperMetadata]] = {}
    unresolved: list[tuple[str, PaperCandidate, Exception]] = []
    post_enrichment_duplicates = 0
    for preliminary_id, candidate in unique.items():
        canonical_ready_id = existing_aliases.get(preliminary_id)
        if canonical_ready_id is not None:
            continue
        try:
            metadata = _invoke_enricher(enricher, candidate)
        except Exception as error:
            unresolved.append((preliminary_id, candidate, error))
            continue
        record_id = stable_record_id(metadata.doi, metadata.arxiv_id, metadata.canonical_url, metadata.title)
        previous = resolved.get(record_id)
        if previous is not None:
            post_enrichment_duplicates += 1
        if previous is None or preliminary_id < previous[0]:
            resolved[record_id] = (preliminary_id, candidate, metadata)

    def reconcile_identity(preliminary_id: str, canonical_id: str) -> None:
        """Migrate a legacy URL fallback/retry to a resolved DOI/arXiv identity."""
        if preliminary_id == canonical_id:
            return
        legacy = by_id.get(preliminary_id)
        if legacy is not None and legacy.status != "ready":
            by_id.pop(preliminary_id)
        legacy_retry = retries.pop(preliminary_id, None)
        if legacy_retry is None:
            return
        current_retry = retries.get(canonical_id)
        if current_retry is None or legacy_retry.attempts > current_retry.attempts:
            retries[canonical_id] = legacy_retry

    def record_failure(record_id: str, candidate: PaperCandidate, error: Exception) -> None:
        nonlocal deferred, metadata_only
        previous = retries.get(record_id, RetryEntry(0, today, "unknown_error"))
        retry = RetryEntry(previous.attempts + 1, today, _error_category(error, "metadata_error"))
        retries[record_id] = retry
        if retry.attempts < 3:
            deferred += 1
            return
        try:
            record = _fallback_record(candidate, record_id, timestamp)
            validate_public_record(record.to_public_dict())
        except Exception:
            deferred += 1
            return
        by_id[record_id] = record
        metadata_only += 1

    for record_id, candidate, error in unresolved:
        old = by_id.get(record_id)
        if old is not None and old.status == "ready":
            continue
        if old is None:
            new += 1
        record_failure(record_id, candidate, error)

    for record_id, (preliminary_id, candidate, metadata) in sorted(resolved.items()):
        reconcile_identity(preliminary_id, record_id)
        old = by_id.get(record_id)
        if old is not None and old.status == "ready":
            continue
        if old is None:
            new += 1
        try:
            summary = _invoke_summarizer(summarizer, metadata, settings)
            record = _ready_record(metadata, candidate, summary, record_id, timestamp)
            validate_public_record(record.to_public_dict())
        except Exception as error:
            record_failure(record_id, candidate, error)
            continue
        else:
            retries.pop(record_id, None)
            summarized += 1
        by_id[record_id] = record

    final_records = _sort_records(list(by_id.values()))
    state_changed = final_records != _sort_records(records) or retries != original_retries
    generated_at = timestamp if state_changed else existing_payload["generated_at"]
    _feed_payload(final_records, generated_at or timestamp)
    changed = state_changed
    if preview_path is not None:
        write_feed_atomic(preview_path, final_records, generated_at)
    if publish and changed:
        _stage_and_publish(Path(feed_path), Path(retry_path), final_records, retries, generated_at)
    return RunSummary(len(raw_messages), len(candidates), len(candidates) - len(unique) + post_enrichment_duplicates, new, summarized, deferred, metadata_only, changed)


def _fixture_functions():
    """Offline deterministic adapters for the default synthetic-fixture preview."""
    def fixture_enricher(candidate):
        return metadata_from_candidate(candidate)
    def fixture_summarizer(_metadata):
        return PaperSummary(
            relevance="weak",
            en=LocalizedSummary("Synthetic fixture summary.", ("Synthetic public evidence.", "No live services were contacted."), "A local preview only.", ("Synthetic",)),
            zh=LocalizedSummary("合成夹具摘要。", ("使用合成公开证据。", "未连接实时服务。"), "仅用于本地预览。", ("合成",)),
        )
    return fixture_enricher, fixture_summarizer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("fixture", "imap"), default="fixture")
    parser.add_argument("--lookback-days", choices=(7, 30), type=int, default=7)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--no-publish", action="store_false", dest="publish")
    parser.set_defaults(publish=False)
    parser.add_argument("--preview-output", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    settings = Settings.from_env(require_credentials=args.source == "imap")
    now = datetime.now(timezone.utc)
    if args.source == "imap":
        messages = fetch_alert_messages(settings, (now - timedelta(days=args.lookback_days)).date())
        summary = run_pipeline(settings, messages, root / "assets/data/paper-feed.json", root / "paper_feed/state/retries.json", args.publish, now, args.preview_output)
    else:
        messages = [(root / "tests/fixtures/scholar_alert.txt.eml").read_bytes()]
        fixture_enricher, fixture_summarizer = _fixture_functions()
        summary = run_pipeline(settings, messages, root / "assets/data/paper-feed.json", root / "paper_feed/state/retries.json", args.publish, now, args.preview_output, fixture_enricher, fixture_summarizer)
    print(json.dumps(summary.to_dict(), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
