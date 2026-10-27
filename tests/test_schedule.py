"""Delayed cron runs should publish once, retry failures and respect local days."""
import datetime as dt
import tempfile
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from scripts.check_schedule import production_due, latest_slot, published_at

UTC = dt.timezone.utc


def instant(value):
    return dt.datetime.fromisoformat(value).astimezone(UTC)


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(enabled=True, interval_hours=3, start_hour_local=0,
                             timezone='Europe/Vienna', days='daily')

    def test_observed_late_run_catches_missed_six_oclock(self):
        due, slot, _ = production_due(self.settings, instant('2026-10-27T07:21:00+01:00'),
                                      instant('2026-10-27T02:04:00+01:00'))
        self.assertTrue(due)
        self.assertEqual(slot, instant('2026-10-27T06:00:00+01:00'))

    def test_no_duplicate_after_catchup_or_manual_publication(self):
        for published in ('2026-10-27T07:21:00+01:00', '2026-10-27T06:00:00+01:00'):
            with self.subTest(published=published):
                self.assertFalse(production_due(self.settings, instant('2026-10-27T08:17:00+01:00'), instant(published))[0])

    def test_multiple_missed_slots_produce_only_latest_edition(self):
        due, slot, _ = production_due(self.settings, instant('2026-10-27T10:17:00+01:00'), instant('2026-10-26T02:04:00+01:00'))
        self.assertTrue(due)
        self.assertEqual(slot, instant('2026-10-27T09:00:00+01:00'))

    def test_failed_attempt_does_not_consume_slot(self):
        previous = instant('2026-10-27T02:04:00+01:00')
        for hour in (6, 7, 8):
            self.assertTrue(production_due(self.settings, instant(f'2026-10-27T{hour:02d}:17:00+01:00'), previous)[0])

    def test_next_slot_becomes_due(self):
        self.assertTrue(production_due(self.settings, instant('2026-10-27T09:17:00+01:00'), instant('2026-10-27T07:21:00+01:00'))[0])

    def test_disabled_and_manual_override(self):
        self.settings['enabled'] = False
        now = instant('2026-10-27T07:21:00+01:00')
        self.assertFalse(production_due(self.settings, now)[0])
        self.assertTrue(production_due(self.settings, now, manual=True)[0])

    def test_weekday_and_weekend_restrictions(self):
        for days, expected in (('weekdays', False), ('weekends', True)):
            self.settings['days'] = days
            self.assertEqual(production_due(self.settings, instant('2026-10-31T10:00:00+01:00'))[0], expected)

    def test_daily_before_start_catches_previous_day(self):
        self.settings.update(interval_hours=24, start_hour_local=8)
        self.assertEqual(latest_slot(self.settings, instant('2026-10-27T07:00:00+01:00')), instant('2026-10-26T08:00:00+01:00'))

    def test_spring_gap_is_skipped(self):
        self.settings.update(interval_hours=24, start_hour_local=2)
        self.assertEqual(latest_slot(self.settings, instant('2026-03-29T03:30:00+02:00')), instant('2026-03-28T02:00:00+01:00'))

    def test_autumn_repeated_hour_publishes_once(self):
        self.settings.update(interval_hours=1)
        first = instant('2026-10-25T02:17:00+02:00')
        second = instant('2026-10-25T02:17:00+01:00')
        self.assertEqual(latest_slot(self.settings, first), latest_slot(self.settings, second))
        self.assertFalse(production_due(self.settings, second, first)[0])

    def test_missing_or_future_publication_does_not_block(self):
        now = instant('2026-10-27T07:21:00+01:00')
        for previous in (None, now + dt.timedelta(days=1)):
            self.assertTrue(production_due(self.settings, now, previous)[0])

    def test_rss_timestamp_and_malformed_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'feed.xml'
            self.assertIsNone(published_at(path))
            path.write_text('<rss><channel><item><pubDate>Tue, 27 Oct 2026 01:04:25 +0000</pubDate></item></channel></rss>')
            self.assertEqual(published_at(path), instant('2026-10-27T01:04:25+00:00'))
            for value in ('broken', '<rss><channel/></rss>', '<rss><channel><item><pubDate>invalid</pubDate></item></channel></rss>'):
                path.write_text(value)
                self.assertIsNone(published_at(path))

    def test_invalid_configuration_rejected_even_for_manual_runs(self):
        for field, value in (('interval_hours', 5), ('interval_hours', True), ('start_hour_local', 24), ('days', 'sometimes')):
            settings = {**self.settings, field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                production_due(settings, instant('2026-10-27T07:00:00+01:00'), manual=True)

    def test_command_line_emits_github_output(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(source / 'scripts', root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'config.json').write_text('{"production_version":"1.0","automation":{"enabled":false}}')
            output = root / 'output'
            for event, expected in (('schedule', 'false'), ('workflow_dispatch', 'true')):
                output.write_text('')
                env = {**os.environ, 'GITHUB_EVENT_NAME': event, 'GITHUB_OUTPUT': str(output)}
                result = subprocess.run([sys.executable, str(root / 'scripts/check_schedule.py')], env=env, capture_output=True, text=True, check=True)
                self.assertEqual(output.read_text(), 'due=' + expected + '\n')
                self.assertIn('Production ' + ('enabled' if expected == 'true' else 'skipped'), result.stdout)
