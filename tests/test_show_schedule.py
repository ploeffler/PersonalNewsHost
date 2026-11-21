"""Workflow minute budget and per-show planning (T070)."""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import feed_resilience as fr  # noqa: E402
import show_schedule as ss  # noqa: E402

WORKFLOWS = ROOT / '.github/workflows'


class CronTests(unittest.TestCase):
    def test_runs_per_month(self):
        self.assertEqual(ss.runs_per_month('17 * * * *'), 720)
        self.assertEqual(ss.runs_per_month('7,22,37,52 * * * *'), 2880)
        self.assertEqual(ss.runs_per_month('5 6,11,19 * * *'), 90)
        self.assertEqual(ss.runs_per_month('*/30 */6 * * *'), 240)
        self.assertEqual(ss.runs_per_month('0 9 * * 1-5'), 22)  # 30 days from Monday 2026-01-05

    def test_cron_fields_and_errors(self):
        cron = ss.parse_cron('0 9 * * 7')
        self.assertTrue(ss.cron_matches(cron, dt.datetime(2026, 1, 4, 9, 0)))  # Sunday
        for bad in ('* * * *', '60 * * * *', '*/0 * * * *', '1-0 * * * *'):
            with self.assertRaises(ValueError):
                ss.parse_cron(bad)

    def test_editions_per_month(self):
        self.assertEqual(ss.editions_per_month({'enabled': True, 'interval_hours': 3}), 240)
        self.assertEqual(ss.editions_per_month({'enabled': True, 'interval_hours': 24, 'days': 'weekdays'}), 21)
        self.assertEqual(ss.editions_per_month({'enabled': False}), 0)
        with self.assertRaises(ValueError):
            ss.editions_per_month({'interval_hours': 5})


class BudgetTests(unittest.TestCase):
    def test_routine_workflows_have_timeouts_and_concurrency(self):
        measured = json.loads((ROOT / 'planning/workflow-minutes.json').read_text())['workflows']
        for name in measured:
            info = ss.workflow_info(WORKFLOWS / name)
            self.assertTrue(info['concurrency'], name)
            self.assertTrue(all(info['timeouts'].values()), name)

    def test_scheduled_workflows_skip_work_when_nothing_is_due(self):
        news = (WORKFLOWS / 'news.yml').read_text()
        check = news.index('- name: Check configured production schedule')
        self.assertLess(check, news.index('- name: Validate production configuration'))
        self.assertLess(check, news.index('- name: Test provider configuration contracts'))
        for name in ('Validate production configuration', 'Test provider configuration contracts'):
            block = news[news.index('- name: ' + name):]
            self.assertIn("if: steps.schedule.outputs.due == 'true'", block.split('\n')[1])
        short = (WORKFLOWS / 'short-updates.yml').read_text()
        block = short[short.index('- name: Test short update and Telegram rules'):]
        self.assertIn("if: github.event_name != 'schedule'", block.split('\n')[1])

    def test_parser_matches_yaml_view(self):
        info = ss.workflow_info(WORKFLOWS / 'fork-sync.yml')
        self.assertEqual(info['crons'], ['17 3 * * *'])
        self.assertEqual(info['timeouts'], {'check': 15, 'synchronize': 15})
        self.assertTrue(info['concurrency'])
        self.assertTrue(ss.workflow_info(WORKFLOWS / 'foundation-ci.yml')['push'])

    def test_budget_is_documented_and_current(self):
        result = ss.budget(config=json.loads((ROOT / 'config.json').read_text()))
        names = {row['workflow'] for row in result['workflows']}
        self.assertTrue({'news.yml', 'short-updates.yml', 'fork-sync.yml'} <= names)
        doc = (ROOT / 'docs/guide/show-planung.md').read_text()
        self.assertIn(f"**{result['total_expected']}**", doc, 'run: python3 scripts/show_schedule.py budget')
        # Public repository: standard runners are free; private quota is reported separately.
        self.assertIsNone(json.loads((ROOT / 'planning/workflow-minutes.json').read_text())['quota']['public_repository'])

    def test_private_profile_fits_the_free_quota(self):
        """The documented private profile (30-min updates, 3 editions/day) stays under 2000 minutes."""
        doc = (ROOT / 'docs/guide/show-planung.md').read_text()
        self.assertIn('Privates Repository', doc)
        updates = ss.runs_per_month('7,37 5-22 * * *') * 1   # every 30 min, 6–24 Uhr MEZ, ~1 billed min
        news = ss.runs_per_month('5 5,10,18 * * *') * 5         # three fixed editions per day
        fork_sync = ss.runs_per_month('17 3 * * *') * 2
        ci = 100 * 3                                             # pushes with foundation checks
        self.assertEqual((updates, news, fork_sync), (1080, 450, 60))
        self.assertLess(updates + news + fork_sync + ci, 2000)

    def test_show_rows(self):
        config = json.loads((ROOT / 'config.shows.example.json').read_text())
        for show in config['shows']:
            show['schedule'] = {'enabled': True, 'interval_hours': 12}
        result = ss.budget(config=config)
        self.assertEqual([s['editions'] for s in result['shows']], [60, 60])
        self.assertEqual(result['shows'][0]['minutes_if_github'], 300)


class CrontabTests(unittest.TestCase):
    def test_one_trigger_per_show_with_locks(self):
        config = json.loads((ROOT / 'config.shows.example.json').read_text())
        config['shows'][0]['schedule'] = {'enabled': True, 'interval_hours': 8, 'start_hour_local': 6,
                                          'timezone': 'Europe/Vienna'}
        config['shows'][1]['schedule'] = {'enabled': True, 'interval_hours': 24, 'start_hour_local': 18,
                                          'days': 'weekdays', 'timezone': 'Europe/Vienna'}
        text = ss.crontab(config, root=Path('/srv/pnh'))
        lines = [line for line in text.splitlines() if line and not line.startswith('#')]
        self.assertEqual(lines[0], 'CRON_TZ=Europe/Vienna')
        self.assertTrue(lines[1].startswith('5 6,14,22 * * * cd /srv/pnh && '))
        self.assertTrue(lines[3].startswith('5 18 * * 1-5 '))
        self.assertIn('flock -n /srv/pnh/.cache/locks/show-main.lock flock -w 3000 /srv/pnh/.cache/locks/render.lock', lines[1])
        self.assertIn('--show technology', lines[3])

    def test_disabled_show_is_commented(self):
        text = ss.crontab(json.loads((ROOT / 'config.shows.example.json').read_text()), root=Path('/x'))
        self.assertIn('# main: automation disabled', text)


class FeedReuseTests(unittest.TestCase):
    def test_second_script_in_the_same_run_reuses_the_download(self):
        import xml.etree.ElementTree as ET
        body = b'<rss><channel><item><title>A</title></item></channel></rss>'
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            fetch = lambda: calls.append(1) or body  # noqa: E731
            import time
            now = time.time()
            fr.load_feed('https://x.example/rss', fetch, ET.fromstring, {}, tmp, now)
            fr.load_feed('https://x.example/rss', fetch, ET.fromstring, {}, tmp, now + 60)
            self.assertEqual(len(calls), 1)
            fr.load_feed('https://x.example/rss', fetch, ET.fromstring, {}, tmp, now + 600)
            self.assertEqual(len(calls), 2)
            fr.load_feed('https://x.example/rss', fetch, ET.fromstring,
                         {'feed_resilience': {'reuse_seconds': 0}}, tmp, now + 601)
            self.assertEqual(len(calls), 3)


if __name__ == '__main__':
    unittest.main()
