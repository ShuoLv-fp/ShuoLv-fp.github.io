"""Immutable contracts that keep private alert data out of the public feed."""

from dataclasses import dataclass
from typing import Literal, Optional, Tuple


EvidenceType = Literal["abstract", "snippet", "metadata", "unavailable"]
Relevance = Literal["high", "transferable", "weak"]
RecordStatus = Literal["ready", "summary_unavailable"]


@dataclass(frozen=True)
class PaperCandidate:
    title: str
    authors: Tuple[str, ...]
    venue: str
    year: Optional[int]
    canonical_url: str
    alert_date: str
    snippet: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None


@dataclass(frozen=True)
class PaperMetadata:
    title: str
    authors: Tuple[str, ...]
    venue: str
    year: Optional[int]
    canonical_url: str
    doi: Optional[str]
    arxiv_id: Optional[str]
    abstract: str
    evidence_type: EvidenceType


@dataclass(frozen=True)
class LocalizedSummary:
    core_conclusion: str
    key_points: Tuple[str, ...]
    research_connection: str
    tags: Tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "core_conclusion": self.core_conclusion,
            "key_points": list(self.key_points),
            "research_connection": self.research_connection,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class PaperSummary:
    relevance: Relevance
    en: LocalizedSummary
    zh: LocalizedSummary


@dataclass(frozen=True)
class PaperRecord:
    record_id: str
    title: str
    authors: Tuple[str, ...]
    venue: str
    year: Optional[int]
    canonical_url: str
    alert_date: str
    ingested_at: str
    evidence_type: EvidenceType
    relevance: Relevance
    en: LocalizedSummary
    zh: LocalizedSummary
    status: RecordStatus

    def to_public_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "title": self.title,
            "authors": list(self.authors),
            "venue": self.venue,
            "year": self.year,
            "canonical_url": self.canonical_url,
            "alert_date": self.alert_date,
            "ingested_at": self.ingested_at,
            "evidence_type": self.evidence_type,
            "relevance": self.relevance,
            "en": self.en.to_dict(),
            "zh": self.zh.to_dict(),
            "status": self.status,
        }


@dataclass(frozen=True)
class RetryEntry:
    attempts: int
    last_attempt_date: str
    error_category: str

    def to_dict(self) -> dict:
        return {
            "attempts": self.attempts,
            "last_attempt_date": self.last_attempt_date,
            "error_category": self.error_category,
        }
