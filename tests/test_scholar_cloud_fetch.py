import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


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
