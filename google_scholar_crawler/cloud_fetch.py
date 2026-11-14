"""Fetch and validate a public Scholar profile with bounded HTTP requests."""

import logging
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


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
        if result.returncode != 0 or result.stdout.strip() != '200':
            raise RuntimeError(f'curl HTTP {result.stdout.strip() or "unavailable"}, exit {result.returncode}')
        return path.read_bytes()


def fetch_browser(url):
    from curl_cffi import requests
    response = requests.get(url, impersonate='chrome', timeout=25,
                            headers={'Accept-Language': 'en-US,en;q=0.9'})
    if response.status_code != 200:
        raise RuntimeError(f'browser transport HTTP {response.status_code}')
    return response.content


def parse_provider(data, scholar_id):
    parameters = data.get('search_parameters', {})
    if (data.get('search_metadata', {}).get('status') != 'Success' or
            parameters.get('engine') != 'google_scholar_author' or
            parameters.get('author_id') != scholar_id):
        raise ValueError('Provider did not return the requested Google Scholar search')
    name = data.get('author', {}).get('name')
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Provider response has no author name')
    author = {'scholar_id': scholar_id, 'name': name,
              'source': 'google-scholar-via-serpapi', 'publications': {}}
    fields = {'citations': 'citedby', 'h_index': 'hindex', 'i10_index': 'i10index'}
    for row in data.get('cited_by', {}).get('table', []):
        for label, field in fields.items():
            if label in row:
                value = row[label].get('all')
                if type(value) is not int or value < 0:
                    raise ValueError('Provider returned an invalid Scholar metric')
                author[field] = value
    if 'citedby' not in author or 'hindex' not in author:
        raise ValueError('Provider citation total or h-index is missing')
    for article in data.get('articles', []):
        paper_id = article.get('citation_id', '')
        value = article.get('cited_by', {}).get('value', 0)
        if not paper_id.startswith(scholar_id + ':') or type(value) is not int or value < 0:
            raise ValueError('Provider publication ID or count is invalid')
        author['publications'][paper_id] = {
            'author_pub_id': paper_id, 'num_citations': value,
            'bib': {'title': article.get('title', ''), 'pub_year': article.get('year', '')},
        }
    author['publications_complete'] = not bool(data.get('serpapi_pagination', {}).get('next'))
    return author


def fetch_provider(scholar_id, api_key):
    query = urlencode({'engine': 'google_scholar_author', 'author_id': scholar_id,
                       'hl': 'en', 'no_cache': 'true', 'api_key': api_key})
    request = Request('https://serpapi.com/search.json?' + query,
                      headers={'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'SerpAPI returned HTTP {error.code}') from None
    except (URLError, OSError, ValueError):
        # Request URLs contain the key; never include them in logs or tracebacks.
        raise RuntimeError('SerpAPI request failed or returned invalid JSON') from None
    try:
        return parse_provider(data, scholar_id)
    except (AttributeError, TypeError, KeyError, ValueError):
        raise RuntimeError('SerpAPI did not return valid Google Scholar metrics') from None


def fetch_author(scholar_id):
    api_key = os.environ.get('SERPAPI_API_KEY', '').strip()
    if api_key:
        try:
            return fetch_provider(scholar_id, api_key)
        except RuntimeError as error:
            logging.info('%s; trying direct Scholar access', error)
    url = 'https://scholar.google.com/citations?' + urlencode({'user': scholar_id, 'hl': 'en'})
    failures = []
    for attempt in range(3):
        if attempt:
            time.sleep(5 * attempt)
        for transport in (fetch_curl, fetch_browser):
            try:
                author = parse_profile(transport(url), scholar_id)
                logging.info('Validated Google Scholar profile: citations=%s h-index=%s', author['citedby'], author['hindex'])
                return author
            except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
                failures.append(str(error))
                logging.info('Scholar request attempt %s did not return a valid profile: %s', attempt + 1, error)
            except Exception as error:
                # curl_cffi transport exceptions are optional until this path is used.
                failures.append(type(error).__name__)
                logging.info('Scholar transport attempt %s failed: %s', attempt + 1, type(error).__name__)
    raise RuntimeError('No valid Google Scholar profile after bounded retries: ' + '; '.join(failures))
