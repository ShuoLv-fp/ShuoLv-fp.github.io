import socket
import unittest
from unittest.mock import patch

import httpx

from paper_feed.metadata import (
    MAX_RESPONSE_BYTES,
    enrich_candidate,
    is_safe_public_url,
    metadata_from_candidate,
)
from paper_feed.models import PaperCandidate


class MetadataTests(unittest.TestCase):
    def candidate(self, **changes):
        values = {
            "title": "Alert title",
            "authors": ("Alert Author",),
            "venue": "Alert venue",
            "year": 2025,
            "canonical_url": "https://papers.example/article",
            "alert_date": "2026-09-09",
            "snippet": "Email snippet.",
            "doi": None,
            "arxiv_id": None,
        }
        values.update(changes)
        return PaperCandidate(**values)

    def mock_client(self, handler):
        return httpx.Client(transport=httpx.MockTransport(handler))

    def test_rejects_non_public_targets(self):
        for url in (
            "file:///etc/passwd", "https://user:pass@example.com/x",
            "http://127.0.0.1/x", "http://169.254.169.254/x",
            "http://192.168.1.1/x", "http://[::1]/x", "https://localhost/x",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_safe_public_url(url))

    @patch("paper_feed.metadata.socket.getaddrinfo")
    def test_accepts_https_hostname_resolving_only_to_public_addresses(self, getaddrinfo):
        getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        self.assertTrue(is_safe_public_url("https://example.com/paper"))

    def test_doi_metadata_has_first_priority(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://api.crossref.org/works/10.1000%2Fexample")
            return httpx.Response(200, json={"message": {
                "title": ["DOI title"], "author": [{"given": "Ada", "family": "Lovelace"}],
                "container-title": ["DOI Journal"], "published": {"date-parts": [[2024]]},
                "abstract": "<jats:p>Public abstract text.</jats:p>", "DOI": "10.1000/example",
            }})

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(doi="https://doi.org/10.1000/example"), client)
        self.assertEqual(metadata.title, "DOI title")
        self.assertEqual(metadata.authors, ("Ada Lovelace",))
        self.assertEqual(metadata.evidence_type, "abstract")
        self.assertEqual(metadata.abstract, "Public abstract text.")

    def test_extracts_doi_from_candidate_snippet(self):
        def handler(request):
            self.assertEqual(request.url.host, "api.crossref.org")
            return httpx.Response(200, json={"message": {"title": ["Snippet DOI"], "abstract": "Public abstract text."}})

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(snippet="See doi:10.1000/from-snippet."), client)
        self.assertEqual(metadata.title, "Snippet DOI")

    def test_arxiv_fallback_uses_atom_abstract(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://export.arxiv.org/api/query?id_list=2401.12345")
            return httpx.Response(200, text="""<?xml version='1.0'?>
                <feed xmlns='http://www.w3.org/2005/Atom'><entry>
                <title> arXiv title </title><summary> Public abstract text. </summary>
                <author><name>Ada Lovelace</name></author><published>2024-01-01T00:00:00Z</published>
                <id>http://arxiv.org/abs/2401.12345</id></entry></feed>""")

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(arxiv_id="arXiv:2401.12345"), client)
        self.assertEqual(metadata.title, "arXiv title")
        self.assertEqual(metadata.arxiv_id, "2401.12345")
        self.assertEqual(metadata.evidence_type, "abstract")

    def test_falls_through_from_doi_to_arxiv_when_doi_has_no_abstract(self):
        calls = []

        def handler(request):
            calls.append(request.url.host)
            if request.url.host == "api.crossref.org":
                return httpx.Response(404)
            return httpx.Response(200, text="""<feed xmlns='http://www.w3.org/2005/Atom'><entry>
                <title>arXiv title</title><summary>Public abstract text.</summary></entry></feed>""")

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(doi="10.1000/missing", arxiv_id="2401.12345"), client)
        self.assertEqual(calls, ["api.crossref.org", "export.arxiv.org"])
        self.assertEqual(metadata.evidence_type, "abstract")

    def test_doi_without_abstract_preserves_email_snippet_after_fallbacks(self):
        def handler(request):
            if request.url.host == "api.crossref.org":
                return httpx.Response(200, json={"message": {"title": ["DOI title"], "DOI": "10.1000/example"}})
            return httpx.Response(404)

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(doi="10.1000/example", canonical_url="https://localhost/paper"), client)
        self.assertEqual(metadata.title, "DOI title")
        self.assertEqual((metadata.abstract, metadata.evidence_type), ("Email snippet.", "snippet"))

    def test_pubmed_fallback_uses_europe_pmc(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query=EXT_ID%3A12345678%20AND%20SRC%3AMED")
            return httpx.Response(200, json={"resultList": {"result": [{
                "title": "PubMed title", "authorString": "Ada Lovelace, Grace Hopper",
                "journalTitle": "Public Medicine", "pubYear": "2023", "abstractText": "Public abstract text.",
                "doi": "10.1000/pubmed",
            }]}})

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(canonical_url="https://pubmed.ncbi.nlm.nih.gov/12345678/"), client)
        self.assertEqual(metadata.title, "PubMed title")
        self.assertEqual(metadata.evidence_type, "abstract")

    def test_openalex_fallback_is_used_after_identifier_sources(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://api.openalex.org/works/https%3A%2F%2Fpapers.example%2Farticle")
            return httpx.Response(200, json={
                "title": "OpenAlex title", "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
                "primary_location": {"source": {"display_name": "Open Journal"}},
                "publication_year": 2022,
                "abstract_inverted_index": {"Public": [0], "abstract": [1], "text.": [2]},
                "doi": "https://doi.org/10.1000/openalex",
            })

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(), client)
        self.assertEqual(metadata.title, "OpenAlex title")
        self.assertEqual(metadata.abstract, "Public abstract text.")

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_landing_page_fallback_follows_guarded_redirect_and_reads_public_meta(self, _safe):
        def handler(request):
            if request.url.host == "www.nature.com":
                return httpx.Response(302, headers={"location": "https://link.springer.com/paper"})
            return httpx.Response(200, text="""
                <meta name='citation_title' content='Landing title'>
                <meta name='citation_author' content='Ada Lovelace'>
                <meta name='citation_publication_date' content='2021-04-05'>
                <meta name='description' content='Public abstract text.'>
            """)

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(canonical_url="https://www.nature.com/article"), client)
        self.assertEqual(metadata.title, "Landing title")
        self.assertEqual(metadata.evidence_type, "abstract")

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_landing_keeps_its_bibliographic_metadata_without_abstract(self, _safe):
        def handler(request):
            return httpx.Response(200, text="<meta name='citation_title' content='Landing title'><meta name='citation_author' content='Ada Lovelace'>")

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(canonical_url="https://www.nature.com/article"), client)
        self.assertEqual(metadata.title, "Landing title")
        self.assertEqual(metadata.authors, ("Ada Lovelace",))
        self.assertEqual((metadata.abstract, metadata.evidence_type), ("Email snippet.", "snippet"))

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_untrusted_landing_host_is_never_requested(self, _safe):
        def handler(request):
            if request.url.host == "api.openalex.org":
                return httpx.Response(404)
            self.fail("untrusted landing URL must not be fetched")

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(canonical_url="https://attacker.example/paper"), client)
        self.assertEqual(metadata.evidence_type, "snippet")

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_landing_rejects_more_than_three_redirects(self, _safe):
        def handler(request):
            number = int(request.url.path.rsplit("/", 1)[-1])
            return httpx.Response(302, headers={"location": f"https://papers.example/{number + 1}"})

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(canonical_url="https://papers.example/0"), client)
        self.assertEqual(metadata.evidence_type, "snippet")
        self.assertEqual(metadata.abstract, "Email snippet.")

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_landing_rejects_oversized_response_body(self, _safe):
        def handler(request):
            return httpx.Response(200, content=b"x" * (MAX_RESPONSE_BYTES + 1))

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(), client)
        self.assertEqual(metadata.evidence_type, "snippet")

    @patch("paper_feed.metadata.is_safe_public_url", return_value=True)
    def test_network_timeout_returns_safe_snippet_fallback(self, _safe):
        def handler(request):
            raise httpx.ReadTimeout("timed out", request=request)

        with self.mock_client(handler) as client:
            metadata = enrich_candidate(self.candidate(), client)
        self.assertEqual((metadata.abstract, metadata.evidence_type), ("Email snippet.", "snippet"))

    def test_metadata_from_candidate_uses_cleaned_snippet_only_when_available(self):
        snippet = metadata_from_candidate(self.candidate(snippet="  Email\n snippet.  "))
        empty = metadata_from_candidate(self.candidate(snippet=" \n "))
        self.assertEqual((snippet.abstract, snippet.evidence_type), ("Email snippet.", "snippet"))
        self.assertEqual((empty.abstract, empty.evidence_type), ("", "unavailable"))


if __name__ == "__main__":
    unittest.main()
