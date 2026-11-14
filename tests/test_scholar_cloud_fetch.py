import importlib.util
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError


SCRIPT = Path('google_scholar_crawler/cloud_fetch.py')
PROFILE = '''<html><head><link rel="canonical" href="https://scholar.google.com/citations?user=VAsm0T8AAAAJ&amp;hl=en"></head>
<body><div id="gsc_prf_in">Shuo Lv</div><table id="gsc_rsb_st"><tbody>
<tr><td>Citations</td><td class="gsc_rsb_std">32</td><td class="gsc_rsb_std">32</td></tr>
<tr><td>h-index</td><td class="gsc_rsb_std">2</td><td class="gsc_rsb_std">2</td></tr>
<tr><td>i10-index</td><td class="gsc_rsb_std">1</td><td class="gsc_rsb_std">1</td></tr>
</tbody></table><table><tr class="gsc_a_tr"><td><a class="gsc_a_at" href="/citations?citation_for_view=VAsm0T8AAAAJ:paper">Paper title</a></td>
<td><a class="gsc_a_ac">25</a></td><td class="gsc_a_y">2024</td></tr></table>
<button id="gsc_bpf_more" disabled>Show more</button></body></html>'''


class CloudFetchTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict('os.environ', {'SERPAPI_API_KEY': ''})
        environment.start()
        self.addCleanup(environment.stop)

    def load_module(self):
        self.assertTrue(SCRIPT.exists(), 'Cloud fetcher is required')
        spec = importlib.util.spec_from_file_location('cloud_fetch', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_parses_google_profile_and_publication_counts(self):
        data = self.load_module().parse_profile(PROFILE, 'VAsm0T8AAAAJ')
        self.assertEqual((data['citedby'], data['hindex']), (32, 2))
        self.assertEqual(data['publications']['VAsm0T8AAAAJ:paper']['num_citations'], 25)
        self.assertTrue(data['publications_complete'])

    def test_rejects_block_pages_wrong_author_and_incomplete_metrics(self):
        module = self.load_module()
        for html in ('<html><title>Sorry...</title></html>', PROFILE.replace('VAsm0T8AAAAJ', 'another'),
                     PROFILE.replace('>32</td>', '>unknown</td>'),
                     PROFILE.replace('<td>h-index</td>', '<td>unexpected</td>')):
            with self.subTest(html=html[:60]), self.assertRaises(ValueError):
                module.parse_profile(html, 'VAsm0T8AAAAJ')

    def test_zero_values_are_not_missing_and_partial_publications_are_explicit(self):
        data = self.load_module().parse_profile(PROFILE.replace('>32</td>', '>0</td>').replace('>2</td>', '>0</td>').replace(' disabled', ''), 'VAsm0T8AAAAJ')
        self.assertEqual((data['citedby'], data['hindex']), (0, 0))
        self.assertFalse(data['publications_complete'])

    def test_browser_transport_recovers_after_direct_http_403(self):
        module = self.load_module()
        with patch.object(module, 'fetch_curl', side_effect=RuntimeError('HTTP 403')), patch.object(module, 'fetch_browser', return_value=PROFILE), patch.object(module.time, 'sleep'):
            data = module.fetch_author('VAsm0T8AAAAJ')
        self.assertEqual(data['citedby'], 32)

    def test_all_failed_transports_raise_instead_of_publishing_old_data(self):
        module = self.load_module()
        with patch.object(module, 'fetch_curl', side_effect=RuntimeError('HTTP 403')), patch.object(module, 'fetch_browser', side_effect=RuntimeError('HTTP 403')), patch.object(module.time, 'sleep'):
            with self.assertRaises(RuntimeError):
                module.fetch_author('VAsm0T8AAAAJ')

    def provider_data(self):
        return {
            'search_metadata': {'status': 'Success'},
            'search_parameters': {'engine': 'google_scholar_author', 'author_id': 'VAsm0T8AAAAJ'},
            'author': {'name': 'Shuo Lv'},
            'cited_by': {'table': [{'citations': {'all': 32}}, {'h_index': {'all': 2}}]},
            'articles': [{'title': 'Paper', 'citation_id': 'VAsm0T8AAAAJ:paper',
                          'cited_by': {'value': 25}, 'year': '2024'}],
        }

    def test_configured_provider_supplies_verified_google_metrics(self):
        module = self.load_module()
        self.assertTrue(hasattr(module, 'fetch_provider'))
        with patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-secret'}), patch.object(
            module, 'urlopen', return_value=io.BytesIO(json.dumps(self.provider_data()).encode())
        ) as request, patch.object(module, 'fetch_curl') as direct:
            data = module.fetch_author('VAsm0T8AAAAJ')
        self.assertEqual((data['citedby'], data['hindex']), (32, 2))
        self.assertEqual(data['source'], 'google-scholar-via-serpapi')
        direct.assert_not_called()
        self.assertIn('no_cache=true', request.call_args.args[0].full_url)

    def test_provider_rejects_wrong_author_missing_metrics_or_failed_search(self):
        module = self.load_module()
        self.assertTrue(hasattr(module, 'parse_provider'))
        for field, value in (('search_parameters', {'author_id': 'wrong'}),
                             ('cited_by', {'table': []}),
                             ('search_metadata', {'status': 'Error'})):
            data = copy.deepcopy(self.provider_data())
            data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.parse_provider(data, 'VAsm0T8AAAAJ')

    def test_provider_network_errors_never_expose_api_key(self):
        module = self.load_module()
        self.assertTrue(hasattr(module, 'fetch_provider'))
        with patch.object(module, 'urlopen', side_effect=URLError('https://example.invalid/?api_key=test-secret')):
            with self.assertRaises(RuntimeError) as error:
                module.fetch_provider('VAsm0T8AAAAJ', 'test-secret')
        self.assertNotIn('test-secret', str(error.exception))
