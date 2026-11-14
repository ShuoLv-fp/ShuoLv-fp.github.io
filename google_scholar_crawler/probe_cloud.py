import json
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

URLS = [
    ('reader', 'https://r.jina.ai/https://scholar.google.com/citations?user=VAsm0T8AAAAJ&hl=en'),
    ('uk', 'https://scholar.google.co.uk/citations?user=VAsm0T8AAAAJ&hl=en'),
    ('hk', 'https://scholar.google.com.hk/citations?user=VAsm0T8AAAAJ&hl=en'),
]

def probe(item):
    label, url = item
    try:
        response = requests.get(url, timeout=45, headers={'X-No-Cache':'true'})
        soup = BeautifulSoup(response.content, 'html.parser')
        result = {'client':label, 'status':response.status_code,
                  'metrics':[cell.get_text() for cell in soup.select('#gsc_rsb_st .gsc_rsb_std')]}
        if label == 'reader':
            result['body'] = response.text[:12000]
        print(json.dumps(result), flush=True)
    except Exception as error:
        print(json.dumps({'client':label,'error':str(error)}), flush=True)

with ThreadPoolExecutor(max_workers=3) as executor:
    list(executor.map(probe, URLS))
