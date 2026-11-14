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
    if not summary['metrics']:
        raise SystemExit(1)
except Exception as error:
    print(json.dumps({'client': 'requests', 'error': type(error).__name__}), flush=True)
    raise SystemExit(1)
