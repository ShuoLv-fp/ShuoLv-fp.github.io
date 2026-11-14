"""Fetch and validate a public Scholar profile with bounded HTTP requests."""

import logging
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from bs4 import BeautifulSoup


class ScholarUnavailable(RuntimeError):
    """No validated snapshot is available from the current network."""


class ScholarBlocked(RuntimeError):
    """Google explicitly refused this transport; retry on a later network."""


def count(value):
    text = value.strip().replace(',', '')
    if not re.fullmatch(r'[0-9]+', text):
        raise ValueError('Google Scholar returned a nonnumeric metric')
    return int(text)


def parse_profile(body, scholar_id):
    soup = BeautifulSoup(body, 'html.parser')
    canonical = soup.find('link', rel='canonical')
    if not canonical or parse_qs(urlparse(canonical.get('href', '')).query).get('user') != [scholar_id]:
        title = soup.title.get_text(strip=True)[:120] if soup.title else 'untitled'
        raise ValueError(f'Response is not the requested Google Scholar profile (page: {title})')
    name = soup.select_one('#gsc_prf_in')
    if not name or not name.get_text(strip=True):
        raise ValueError('Google Scholar profile has no author name')
    fields = {'citations': ('citedby', 'citedby5y'),
              'h-index': ('hindex', 'hindex5y'),
              'i10-index': ('i10index', 'i10index5y')}
    author = {'scholar_id': scholar_id, 'name': name.get_text(strip=True),
              'source': 'google-scholar-profile', 'publications': {}}
    for row in soup.select('#gsc_rsb_st tbody tr'):
        cells = row.find_all('td')
        if not cells:
            continue
        label = cells[0].get_text(strip=True).lower()
        if label in fields:
            if len(cells) != 3:
                raise ValueError('Google Scholar metrics table is incomplete')
            for field, cell in zip(fields[label], cells[1:]):
                author[field] = count(cell.get_text())
    if 'citedby' not in author or 'hindex' not in author:
        raise ValueError('Google Scholar citation total or h-index is missing')

    for row in soup.select('.gsc_a_tr'):
        title = row.select_one('.gsc_a_at')
        cited = row.select_one('.gsc_a_ac')
        if title is None or cited is None:
            raise ValueError('Google Scholar publication row is incomplete')
        identifiers = parse_qs(urlparse(title.get('href', '')).query).get('citation_for_view', [])
        if len(identifiers) != 1 or not identifiers[0].startswith(scholar_id + ':'):
            raise ValueError('Google Scholar publication author does not match')
        paper_id = identifiers[0]
        citations = cited.get_text(strip=True).rstrip('*')
        year = row.select_one('.gsc_a_y')
        author['publications'][paper_id] = {
            'author_pub_id': paper_id,
            'num_citations': count(citations) if citations else 0,
            'bib': {'title': title.get_text(strip=True),
                    'pub_year': year.get_text(strip=True) if year else ''},
        }
    more = soup.select_one('#gsc_bpf_more')
    author['publications_complete'] = more is not None and more.has_attr('disabled')
    return author


def fetch_curl(url):
    with tempfile.TemporaryDirectory(prefix='scholar-http-') as directory:
        path = Path(directory) / 'profile.html'
        result = subprocess.run(
            ['curl', '--silent', '--show-error', '--location', '--connect-timeout', '10',
             '--max-time', '25', '--output', str(path), '--write-out', '%{http_code}', url],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip() in ('403', '429'):
            raise ScholarBlocked(f'curl HTTP {result.stdout.strip()}')
        if result.returncode != 0 or result.stdout.strip() != '200':
            raise RuntimeError(f'curl HTTP {result.stdout.strip() or "unavailable"}, exit {result.returncode}')
        return path.read_bytes()


def fetch_browser(url):
    from curl_cffi import requests
    from curl_cffi.requests.exceptions import RequestException
    try:
        response = requests.get(url, impersonate='chrome', timeout=25,
                                headers={'Accept-Language': 'en-US,en;q=0.9'})
    except RequestException as error:
        raise RuntimeError(f'browser transport failed: {type(error).__name__}') from None
    if response.status_code in (403, 429):
        raise ScholarBlocked(f'browser transport HTTP {response.status_code}')
    if response.status_code != 200:
        raise RuntimeError(f'browser transport HTTP {response.status_code}')
    return response.content


def fetch_author(scholar_id):
    url = 'https://scholar.google.com/citations?' + urlencode({'user': scholar_id, 'hl': 'en'})
    failures = []
    blocked = set()
    transports = (fetch_curl, fetch_browser)
    for attempt in range(3):
        if len(blocked) == len(transports):
            break
        if attempt:
            time.sleep(5 * attempt)
        for transport in transports:
            if transport in blocked:
                continue
            try:
                author = parse_profile(transport(url), scholar_id)
                logging.info('Validated Google Scholar profile: citations=%s h-index=%s', author['citedby'], author['hindex'])
                return author
            except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
                if isinstance(error, ScholarBlocked):
                    blocked.add(transport)
                failures.append(str(error))
                logging.info('Scholar request attempt %s did not return a valid profile: %s', attempt + 1, error)
    raise ScholarUnavailable('No valid Google Scholar profile after bounded attempts: ' + '; '.join(failures))
