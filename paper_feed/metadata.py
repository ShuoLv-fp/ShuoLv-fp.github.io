"""Public scholarly metadata enrichment with bounded, SSRF-safe requests."""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from typing import Any
from urllib.parse import quote, urljoin, urlsplit
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

from paper_feed.models import PaperCandidate, PaperMetadata


SOURCE_ORDER = ("doi", "arxiv", "pubmed", "openalex", "landing", "snippet")
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT = httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)
USER_AGENT = "ShuoLv-paper-feed/1.0 (+https://shuolv.github.io/)"
LANDING_ALLOWED_HOSTS = (
    "acm.org", "arxiv.org", "biorxiv.org", "cell.com", "frontiersin.org",
    "ieee.org", "link.springer.com", "medrxiv.org", "nature.com", "nih.gov",
    "plos.org", "pmc.ncbi.nlm.nih.gov", "sciencedirect.com", "science.org",
    "springer.com", "wiley.com",
)
_DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_ARXIV_PATTERN = re.compile(r"(?:arxiv(?:\.org/(?:abs|pdf)/)?\s*:?\s*)?((?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[a-z-]+)?/\d{7})(?:v\d+)?)", re.IGNORECASE)
_PMID_PATTERN = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)|\bpmid\s*:\s*(\d+)", re.IGNORECASE)


def _clean(value: object, limit: int = 8000) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def _doi(value: str | None) -> str | None:
    match = _DOI_PATTERN.search(value or "")
    return match.group(0).rstrip(".,;)\]") if match else None


def _arxiv(value: str | None) -> str | None:
    text = (value or "").strip()
    if "://" in text and "arxiv.org" not in (urlsplit(text).hostname or "").casefold():
        return None
    match = _ARXIV_PATTERN.search(text)
    return match.group(1).casefold() if match else None


def _pmid(value: str) -> str | None:
    match = _PMID_PATTERN.search(value)
    return (match.group(1) or match.group(2)) if match else None


def address_is_public(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return not any((address.is_private, address.is_loopback, address.is_link_local,
                    address.is_multicast, address.is_reserved, address.is_unspecified))


def is_safe_public_url(url: str) -> bool:
    """Return whether an HTTP(S) URL resolves exclusively to public addresses."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port
    except (TypeError, ValueError):
        return False
    if (parts.scheme not in {"http", "https"} or not host or parts.username is not None
            or parts.password is not None or any(char.isspace() for char in url)):
        return False
    host = host.rstrip(".").casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        return False
    try:
        try:
            return address_is_public(host)
        except ValueError:
            addresses = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
            return bool(addresses) and all(address_is_public(item[4][0]) for item in addresses)
    except (OSError, ValueError):
        return False


def _is_trusted_landing_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").rstrip(".").casefold()
    except (TypeError, ValueError):
        return False
    return parts.scheme == "https" and any(host == domain or host.endswith(f".{domain}") for domain in LANDING_ALLOWED_HOSTS) and is_safe_public_url(url)


def metadata_from_candidate(candidate: PaperCandidate) -> PaperMetadata:
    """Create safe no-network fallback metadata from a public candidate."""
    snippet = _clean(candidate.snippet, 4000)
    return PaperMetadata(
        title=_clean(candidate.title, 500), authors=tuple(_clean(author, 500) for author in candidate.authors if _clean(author, 500)),
        venue=_clean(candidate.venue, 1000), year=candidate.year,
        canonical_url=_clean(candidate.canonical_url, 4000), doi=_doi(candidate.doi or candidate.canonical_url),
        arxiv_id=_arxiv(candidate.arxiv_id or candidate.canonical_url), abstract=snippet,
        evidence_type="snippet" if snippet else "unavailable",
    )


def _bounded_request(client: httpx.Client, url: str) -> tuple[int, dict[str, str], bytes] | None:
    """Fetch one prevalidated URL without redirects, enforcing the byte ceiling."""
    try:
        with client.stream("GET", url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, text/html;q=0.8"}, follow_redirects=False, timeout=REQUEST_TIMEOUT) as response:
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > MAX_RESPONSE_BYTES:
                    return None
            return response.status_code, dict(response.headers), bytes(body)
    except (httpx.HTTPError, ValueError):
        return None


def _json_response(client: httpx.Client, url: str) -> dict[str, Any] | None:
    response = _bounded_request(client, url)
    if not response or response[0] != 200:
        return None
    try:
        value = json.loads(response[2])
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _with_fields(base: PaperMetadata, *, title: object = "", authors: tuple[str, ...] = (), venue: object = "", year: object = None, doi: str | None = None, arxiv_id: str | None = None, abstract: object = "") -> PaperMetadata:
    body = _clean(BeautifulSoup(str(abstract or ""), "html.parser").get_text(" ", strip=True), 8000)
    parsed_year = int(year) if str(year or "").isdigit() and 1800 <= int(year) <= 2100 else base.year
    return PaperMetadata(
        title=_clean(title, 500) or base.title, authors=authors or base.authors, venue=_clean(venue, 1000) or base.venue,
        year=parsed_year, canonical_url=base.canonical_url, doi=_doi(doi) or base.doi,
        arxiv_id=_arxiv(arxiv_id) or base.arxiv_id, abstract=body or base.abstract,
        evidence_type="abstract" if body else base.evidence_type,
    )


def _crossref(base: PaperMetadata, client: httpx.Client, doi: str) -> PaperMetadata | None:
    data = _json_response(client, f"https://api.crossref.org/works/{quote(doi, safe='')}")
    message = data.get("message") if data else None
    if not isinstance(message, dict):
        return None
    authors = tuple(_clean(f"{author.get('given', '')} {author.get('family', '')}", 500) for author in message.get("author", []) if isinstance(author, dict))
    date_parts = (message.get("published") or message.get("issued") or {}).get("date-parts", [[]])
    year = date_parts[0][0] if date_parts and date_parts[0] else None
    return _with_fields(base, title=(message.get("title") or [""])[0], authors=tuple(author for author in authors if author), venue=(message.get("container-title") or [""])[0], year=year, doi=message.get("DOI") or doi, abstract=message.get("abstract"))


def _arxiv_metadata(base: PaperMetadata, client: httpx.Client, arxiv_id: str) -> PaperMetadata | None:
    response = _bounded_request(client, f"https://export.arxiv.org/api/query?id_list={quote(arxiv_id, safe='')}")
    if not response or response[0] != 200:
        return None
    try:
        root = ElementTree.fromstring(response[2])
    except ElementTree.ParseError:
        return None
    atom = "{http://www.w3.org/2005/Atom}"
    entry = root.find(f"{atom}entry")
    if entry is None:
        return None
    authors = tuple(_clean(node.text, 500) for node in entry.findall(f"{atom}author/{atom}name") if _clean(node.text, 500))
    return _with_fields(base, title=entry.findtext(f"{atom}title"), authors=authors, year=(entry.findtext(f"{atom}published") or "")[:4], arxiv_id=arxiv_id, abstract=entry.findtext(f"{atom}summary"))


def _pubmed_metadata(base: PaperMetadata, client: httpx.Client, pmid: str) -> PaperMetadata | None:
    query = quote(f"EXT_ID:{pmid} AND SRC:MED", safe="")
    data = _json_response(client, f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query={query}")
    results = ((data or {}).get("resultList") or {}).get("result") or []
    item = results[0] if results and isinstance(results[0], dict) else None
    if not item:
        return None
    authors = tuple(_clean(author, 500) for author in str(item.get("authorString") or "").split(",") if _clean(author, 500))
    return _with_fields(base, title=item.get("title"), authors=authors, venue=item.get("journalTitle"), year=item.get("pubYear"), doi=item.get("doi"), abstract=item.get("abstractText"))


def _openalex_metadata(base: PaperMetadata, client: httpx.Client) -> PaperMetadata | None:
    data = _json_response(client, f"https://api.openalex.org/works/{quote(base.canonical_url, safe='')}")
    if not data:
        return None
    inverted = data.get("abstract_inverted_index") or {}
    # The index positions—not JSON insertion order—determine the source abstract.
    positioned = [(position, word) for word, positions in inverted.items() if isinstance(positions, list) for position in positions]
    abstract = " ".join(word for _, word in sorted(positioned)) if positioned else ""
    authors = tuple(_clean((entry.get("author") or {}).get("display_name"), 500) for entry in data.get("authorships", []) if isinstance(entry, dict))
    location = ((data.get("primary_location") or {}).get("source") or {}).get("display_name")
    return _with_fields(base, title=data.get("title"), authors=tuple(author for author in authors if author), venue=location, year=data.get("publication_year"), doi=data.get("doi"), abstract=abstract)


def _landing_metadata(base: PaperMetadata, client: httpx.Client) -> PaperMetadata | None:
    url = base.canonical_url
    if not _is_trusted_landing_url(url):
        return None
    for _ in range(MAX_REDIRECTS + 1):
        response = _bounded_request(client, url)
        if not response:
            return None
        status, headers, body = response
        if 300 <= status < 400:
            target = headers.get("location")
            if not target:
                return None
            url = urljoin(url, target)
            if not _is_trusted_landing_url(url):
                return None
            continue
        if status != 200:
            return None
        soup = BeautifulSoup(body, "html.parser")
        meta: dict[str, list[str]] = {}
        for node in soup.find_all("meta"):
            key = _clean(node.get("name") or node.get("property"), 100).casefold()
            value = _clean(node.get("content"), 8000)
            if key and value and (key.startswith("citation_") or key.startswith("dc.") or key.startswith("dcterms.") or key.startswith("og:") or key == "description"):
                meta.setdefault(key, []).append(value)
        return _with_fields(base, title=(meta.get("citation_title") or meta.get("dc.title") or meta.get("og:title") or [""])[0], authors=tuple(meta.get("citation_author", [])), venue=(meta.get("citation_journal_title") or meta.get("og:site_name") or [""])[0], year=(meta.get("citation_publication_date") or meta.get("dc.date") or [""])[0][:4], doi=(meta.get("citation_doi") or [None])[0], abstract=(meta.get("citation_abstract") or meta.get("dc.description") or meta.get("dcterms.description") or meta.get("description") or meta.get("og:description") or [""])[0])
    return None


def enrich_candidate(candidate: PaperCandidate, client: httpx.Client) -> PaperMetadata:
    """Enrich in fixed source order; network failures return safe local evidence."""
    metadata = metadata_from_candidate(candidate)
    doi = _doi(candidate.doi) or _doi(candidate.canonical_url) or _doi(candidate.title) or _doi(candidate.snippet)
    arxiv_id = _arxiv(candidate.arxiv_id) or _arxiv(candidate.canonical_url) or _arxiv(candidate.title) or _arxiv(candidate.snippet)
    pmid = _pmid(candidate.canonical_url) or _pmid(candidate.title)
    for adapter, identifier in ((_crossref, doi), (_arxiv_metadata, arxiv_id), (_pubmed_metadata, pmid)):
        if identifier:
            result = adapter(metadata, client, identifier)
            if result:
                metadata = result
                if metadata.evidence_type == "abstract":
                    return metadata
    result = _openalex_metadata(metadata, client)
    if result:
        metadata = result
        if metadata.evidence_type == "abstract":
            return metadata
    result = _landing_metadata(metadata, client)
    return result or metadata
