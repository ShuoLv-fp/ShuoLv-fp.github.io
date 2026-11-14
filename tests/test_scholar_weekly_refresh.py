from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import unittest


class WeeklyRefreshTests(unittest.TestCase):
    def load_module(self):
        script = Path('google_scholar_crawler/weekly_refresh.py')
        self.assertTrue(script.exists(), 'A weekly freshness gate is required')
        spec = importlib.util.spec_from_file_location('weekly_refresh', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def snapshot(self, updated):
        return {'scholar_id': 'VAsm0T8AAAAJ', 'citedby': 32, 'hindex': 2, 'updated': updated}

    def test_recovery_runs_skip_after_this_weeks_success(self):
        module = self.load_module()
        now = datetime(2026, 11, 16, 7, 17, tzinfo=timezone.utc)
        self.assertFalse(module.refresh_due(self.snapshot('2026-11-16T01:20:00+00:00'), now))
        self.assertFalse(module.refresh_due(self.snapshot('2026-11-16 01:20:00'), now))
        self.assertTrue(module.refresh_due(self.snapshot('2026-11-14T07:04:15+00:00'), now))

    def test_week_boundary_uses_shanghai_timezone(self):
        module = self.load_module()
        now = datetime(2026, 11, 16, 1, 17, tzinfo=timezone.utc)
        self.assertFalse(module.refresh_due(self.snapshot('2026-11-15T16:05:00Z'), now))
        self.assertTrue(module.refresh_due(self.snapshot('2026-11-15T15:59:59Z'), now))

    def test_invalid_or_future_snapshots_do_not_suppress_fetching(self):
        module = self.load_module()
        now = datetime(2026, 11, 16, 1, 17, tzinfo=timezone.utc)
        for changes in ({'updated': 'bad'}, {'updated': '2027-01-01T00:00:00Z'},
                        {'scholar_id': 'wrong'}, {'citedby': None}, {'hindex': True}):
            with self.subTest(changes=changes):
                self.assertTrue(module.refresh_due({**self.snapshot('2026-11-16T01:15:00Z'), **changes}, now))
