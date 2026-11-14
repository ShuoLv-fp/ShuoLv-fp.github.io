"""Compare public profile requests on the same hosted network."""

import json
import time

from bs4 import BeautifulSoup
from curl_cffi import requests

from cloud_fetch import parse_profile

AUTHOR = 'VAsm0T8AAAAJ'
BASE = 'https://scholar.google.com'
session = requests.Session(impersonate='chrome')


def probe(label, url):
    try:
        response = session.get(url, timeout=25, headers={'Accept-Language': 'en-US,en;q=0.9'})
        soup = BeautifulSoup(response.content, 'html.parser')
        result = {'client': label, 'status': response.status_code,
                  'title': soup.title.get_text() if soup.title else None,
                  'redirected': response.url != url}
        try:
            author = parse_profile(response.content, AUTHOR)
            result.update(citedby=author['citedby'], hindex=author['hindex'])
        except ValueError:
            result['page_text'] = soup.get_text(' ', strip=True)[:350]
        print(json.dumps(result), flush=True)
    except Exception as error:
        print(json.dumps({'client': label, 'error': type(error).__name__}), flush=True)
    time.sleep(3)


probe('current', BASE + '/citations?user=' + AUTHOR + '&hl=en')
probe('profile-navigation', BASE + '/citations?hl=en&user=' + AUTHOR + '&sortby=pubdate')
probe('homepage', BASE + '/?hl=en')
probe('session-profile', BASE + '/citations?hl=en&user=' + AUTHOR)
