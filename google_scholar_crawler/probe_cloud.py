"""Bounded diagnostic requests for the public Google Scholar profile."""

import json
import subprocess
import tempfile
import time
from pathlib import Path

from bs4 import BeautifulSoup


URL = 'https://scholar.google.com/citations?user=VAsm0T8AAAAJ&hl=en'


def describe(body):
    soup = BeautifulSoup(body, 'html.parser')
    return {
        'title': soup.title.get_text() if soup.title else None,
        'metrics': [cell.get_text() for cell in soup.select('#gsc_rsb_st .gsc_rsb_std')],
        'publications': len(soup.select('.gsc_a_tr')),
    }


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'profile.html'
    started = time.monotonic()
    result = subprocess.run(
        ['curl', '--silent', '--show-error', '--location', '--max-time', '25',
         '--output', str(path), '--write-out', '%{http_code}', URL],
        capture_output=True, text=True, timeout=30,
    )
    summary = {'client': 'curl', 'status': result.stdout, 'exit': result.returncode,
               'seconds': round(time.monotonic() - started, 2)}
    if path.exists():
        summary.update(describe(path.read_bytes()))
    print(json.dumps(summary), flush=True)
    if summary.get('metrics'):
        raise SystemExit(0)

try:
    import requests
    started = time.monotonic()
    response = requests.get(URL, timeout=25, headers={'Accept-Language': 'en-US,en;q=0.9'})
    summary = {'client': 'requests', 'status': response.status_code,
               'seconds': round(time.monotonic() - started, 2), **describe(response.content)}
    print(json.dumps(summary), flush=True)
    if summary['metrics']:
        raise SystemExit(0)
except Exception as error:
    print(json.dumps({'client': 'requests', 'error': type(error).__name__}), flush=True)

from curl_cffi import requests as browser_requests
for label, url in [('chrome', URL), ('chrome-regional', URL.replace('scholar.google.com', 'scholar.google.com.hk'))]:
    try:
        response = browser_requests.get(url, impersonate='chrome', timeout=25)
        summary = {'client': label, 'status': response.status_code, **describe(response.content)}
        print(json.dumps(summary), flush=True)
        if summary['metrics']:
            raise SystemExit(0)
    except Exception as error:
        print(json.dumps({'client': label, 'error': type(error).__name__}), flush=True)

try:
    response = requests.get('https://r.jina.ai/' + URL, timeout=45, headers={'X-No-Cache':'true'})
    print(json.dumps({'client':'jina-reader', 'status':response.status_code, 'body':response.text[:9000]}), flush=True)
except Exception as error:
    print(json.dumps({'client':'jina-reader','error':type(error).__name__}), flush=True)
raise SystemExit(1)
