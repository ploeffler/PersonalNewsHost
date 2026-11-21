import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import feed_resilience as fr  # noqa: E402

URL = 'https://feeds.example.org/news.rss'
RSS = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>'
       b'<item><title>Hochwasser in Linz</title><description>Die Donau steigt weiter. Die Feuerwehr ist im Einsatz.'
       b'</description><link>https://feeds.example.org/a</link></item></channel></rss>')


def http_error(code):
    return urllib.error.HTTPError(URL, code, 'x', {}, None)


class Flaky:
    def __init__(self, *outcomes):
        self.outcomes, self.calls = list(outcomes), 0

    def __call__(self):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class RetryTests(unittest.TestCase):
    def test_transient_classification(self):
        for exc in [urllib.error.URLError('down'), TimeoutError(), ConnectionResetError(), http_error(503), http_error(429)]:
            self.assertTrue(fr.is_transient(exc), exc)
        for exc in [http_error(404), http_error(403), ValueError('bad url'), ET.ParseError('broken')]:
            self.assertFalse(fr.is_transient(exc), exc)

    def test_backoff_then_success(self):
        pauses, fetch = [], Flaky(TimeoutError(), http_error(502), RSS)
        self.assertEqual(fr.fetch_with_retry(fetch, fr.settings_from({}), pauses.append), RSS)
        self.assertEqual((fetch.calls, pauses), (3, [2.0, 6.0]))

    def test_permanent_errors_are_not_retried(self):
        pauses, fetch = [], Flaky(http_error(404), RSS)
        with self.assertRaises(urllib.error.HTTPError):
            fr.fetch_with_retry(fetch, fr.settings_from({}), pauses.append)
        self.assertEqual((fetch.calls, pauses), (1, []))

    def test_settings_are_clamped(self):
        s = fr.settings_from({'feed_resilience': {'attempts': 99, 'backoff_seconds': 'x', 'failure_threshold': 0}})
        self.assertEqual((s['attempts'], s['backoff_seconds'], s['failure_threshold']), (5, [2.0, 6.0], 1))


class FallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def load(self, fetch, now, config=None):
        return fr.load_feed(URL, fetch, ET.fromstring, config or {}, self.root, now, sleep=lambda _: None)

    def test_last_valid_copy_is_used_and_expires(self):
        self.load(lambda: RSS, now=1000)
        cache = self.root / '.cache/feeds' / (fr.feed_key(URL) + '.xml')
        os.utime(cache, (1000, 1000))
        document = self.load(Flaky(TimeoutError(), TimeoutError(), TimeoutError()), now=1000 + 3600)
        self.assertEqual(document.findtext('.//item/title'), 'Hochwasser in Linz')
        with self.assertRaises(TimeoutError):
            self.load(Flaky(TimeoutError(), TimeoutError(), TimeoutError()), now=1000 + 49 * 3600)

    def test_broken_xml_falls_back_and_never_replaces_good_copy(self):
        self.load(lambda: RSS, now=time_now())
        document = self.load(lambda: b'<rss><channel><item>', now=time_now())
        self.assertEqual(document.findtext('.//item/title'), 'Hochwasser in Linz')
        cached = (self.root / '.cache/feeds' / (fr.feed_key(URL) + '.xml')).read_bytes()
        self.assertEqual(cached, RSS)

    def test_without_cache_the_error_propagates(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.load(Flaky(http_error(404)), now=1000)

    def test_health_counts_runs_and_resets_on_success(self):
        state = fr.FeedState(self.root)
        for now in (0, 60, 400, 800):  # two reads in the first run count once
            state.record(URL, False, now, 'TimeoutError')
        entry = state.health()[fr.feed_key(URL)]
        self.assertEqual((entry['failures'], entry['first_failure_at'], entry['host']), (3, 0, 'feeds.example.org'))
        state.record(URL, True, 900)
        self.assertEqual(state.health()[fr.feed_key(URL)]['failures'], 0)
        self.assertNotIn(URL, (self.root / '.cache/feeds/health.json').read_text())


def time_now():
    import time
    return time.time()


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.config = {'title': 'PNH', 'feeds': ['https://ok.example/rss', URL],
                       'feed_resilience': {'notify': {'telegram': True, 'github_issue': True}}}
        state = fr.FeedState(self.root)
        for now in (0, 400, 800):
            state.record(URL, False, now, 'TimeoutError')
        state.record('https://ok.example/rss', False, 800, 'TimeoutError')

    def test_due_after_threshold_and_once_per_interval(self):
        posts = []
        env = {'TELEGRAM_BOT_TOKEN': 't', 'TELEGRAM_ADMIN_CHAT_ID': '42', 'GITHUB_TOKEN': 'g', 'GITHUB_REPOSITORY': 'o/r'}
        sent = fr.notify(self.root, self.config, env, now=1000, post=lambda *a: posts.append(a) or True)
        self.assertEqual(sent, ['telegram', 'github_issue'])
        telegram, issue = posts
        self.assertIn('Feed Nr. 2 (feeds.example.org)', telegram[1]['text'])
        self.assertNotIn('ok.example', telegram[1]['text'])
        self.assertIn('Feed Nr. 2', issue[1]['body'])
        self.assertNotIn('example.org', json.dumps(issue[1]))
        self.assertEqual(fr.notify(self.root, self.config, env, now=2000, post=lambda *a: posts.append(a) or True), [])
        self.assertEqual(len(fr.notify(self.root, self.config, env, now=1000 + 24 * 3600, post=lambda *a: True)), 2)

    def test_without_secrets_nothing_is_sent_or_marked(self):
        self.assertEqual(fr.notify(self.root, self.config, {}, now=1000, post=lambda *a: self.fail('sent')), [])
        self.assertEqual(len(fr.due_notices(self.root, self.config, now=1000)), 1)

    def test_issue_channel_is_opt_in(self):
        config = {**self.config, 'feed_resilience': {}}
        env = {'GITHUB_TOKEN': 'g', 'GITHUB_REPOSITORY': 'o/r'}
        self.assertEqual(fr.notify(self.root, config, env, now=1000, post=lambda *a: self.fail('sent')), [])

    def test_removed_feed_is_not_reported(self):
        config = {**self.config, 'feeds': ['https://ok.example/rss']}
        self.assertEqual(fr.due_notices(self.root, config, now=1000), [])


@unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
class BroadcastTests(unittest.TestCase):
    def test_single_failing_feed_does_not_stop_the_broadcast(self):
        from scripts import generate
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'docs').mkdir()
            (root / 'assets').mkdir()
            cfg = copy.deepcopy(generate.CONFIG)
            cfg.pop('shows', None)
            cfg.setdefault('editorial', {})['pipeline'] = {'enabled': False}
            cfg['editorial']['crosscheck'] = {'enabled': False}
            cfg.update({'title': 'Test', 'feeds': ['https://down.example/rss', URL], 'max_items': 2,
                        'max_description_chars': 60, 'tts_engine': 'espeak', 'voice_pitch_semitones': 0,
                        'station_logo': '', 'media': {'mode': 'off'}})
            cfg['presenter_settings'] = {
                'name': 'Test', 'portrait': 'assets/missing.png', 'background': 'assets/missing.jpg',
                'scenes': {'intro_mode': 'static', 'intro_static_type': 'color', 'intro_seconds': 1, 'outro_seconds': 1}}

            def fetch(url):
                if 'down.example' in url:
                    raise urllib.error.URLError('connection refused')
                return RSS

            def audio(_text, destination):
                with wave.open(str(destination), 'wb') as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(16000)
                    f.writeframes(bytes(16000 * 2 * 2))
            with patch.object(generate, 'ROOT', root), patch.object(generate, 'DOCS', root / 'docs'), \
                    patch.object(generate, 'CONFIG', cfg), patch.object(generate, 'fetch', side_effect=fetch), \
                    patch.object(generate, 'extract_article_text', return_value=''), \
                    patch.object(generate, 'synthesize', side_effect=audio), \
                    patch.object(fr.time, 'sleep') as sleep, patch.dict(generate.FEED_DATES, {}, clear=True):
                generate.main()
            self.assertTrue((root / 'docs/latest.mp4').stat().st_size > 1000)
            backoff = [c.args for c in sleep.call_args_list if c.args in ((2.0,), (6.0,))]
            self.assertEqual(backoff, [(2.0,), (6.0,)])  # three attempts for the failing feed
            health = json.loads((root / '.cache/feeds/health.json').read_text())
            self.assertEqual(health[fr.feed_key('https://down.example/rss')]['failures'], 1)
            self.assertEqual(health[fr.feed_key(URL)]['failures'], 0)


if __name__ == '__main__':
    unittest.main()
