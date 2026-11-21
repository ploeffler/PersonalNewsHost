import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import breaking_news as b  # noqa: E402

NOW = 2_000_000_000


def load_short_updates():
    spec = importlib.util.spec_from_file_location('short_updates_t013', ROOT / 'scripts/short_updates.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate(title, url='https://orf.at/stories/1/', feed='https://rss.orf.at/news.xml', age=120):
    return {'title': title, 'description': 'Die Lage ist unklar. Weitere Informationen folgen.',
            'url': url, 'feed': feed, 'source': url.split('/')[2], 'published_at': NOW - age}


def settings(**breaking):
    return b.settings_from({'short_updates': {'breaking': breaking}})


class BreakingRulesTests(unittest.TestCase):
    def test_defaults_and_clamping(self):
        s = settings(min_sources=9, max_clip_seconds=300, max_per_day=-3, keywords='kein Array')
        self.assertEqual((s['min_sources'], s['max_clip_seconds'], s['max_per_day']), (5, 60, 0))
        self.assertEqual(s['keywords'], [])
        self.assertIn('eilmeldung', b.settings_from({})['keywords'])

    def test_keywords_wildcards_and_exclusions(self):
        s = settings(keywords=['evakuier*', '+++', 'lokbrand'], exclude_keywords=['übung*'])
        hit = lambda title: b.assess(candidate(title), [], s, NOW, 3600)
        self.assertEqual(hit('Wohnhaus in Graz evakuiert'), 'Stichwort')
        self.assertEqual(hit('+++ Zugunglück bei Wels +++'), 'Stichwort')
        self.assertEqual(hit('LOKBRAND auf der Aspangbahn'), 'Stichwort')
        self.assertIsNone(hit('Lokbrandschutz wird verbessert'))
        self.assertIsNone(hit('Schule evakuiert – nur eine Übung'))
        self.assertIsNone(hit('Neue Ausstellung im Museum'))

    def test_breaking_source_by_feed_or_host(self):
        s = settings(keywords=[], sources=['https://rss.orf.at/news.xml', 'apa.at'])
        self.assertEqual(b.assess(candidate('Irgendein Titel'), [], s, NOW, 3600), 'Quelle')
        other = candidate('Irgendein Titel', url='https://www.apa.at/x', feed='https://apa.at/rss')
        self.assertEqual(b.assess(other, [], s, NOW, 3600), 'Quelle')
        self.assertIsNone(b.assess(candidate('Irgendein Titel', feed='https://orf.at/other.xml'), [], s, NOW, 3600))

    def test_min_sources_threshold_needs_independent_publishers(self):
        s = settings(keywords=['evakuiert'], min_sources=2)
        first = candidate('Hochhaus in Linz evakuiert')
        same_host = candidate('Hochhaus in Linz evakuiert', url='https://orf.at/stories/2/')
        other = candidate('Linz: Hochhaus evakuiert, Feuerwehr im Einsatz', url='https://derstandard.at/a')
        stale = candidate('Hochhaus in Linz evakuiert', url='https://kurier.at/a', age=7200)
        self.assertIsNone(b.assess(first, [first, same_host, stale], s, NOW, 3600))
        self.assertEqual(b.assess(first, [first, other], s, NOW, 3600), 'Stichwort')


class SelectionTests(unittest.TestCase):
    def test_daily_limit_survives_five_item_cap(self):
        m = load_short_updates()
        s = settings(keywords=['eilmeldung'], max_per_day=2)
        state = {}
        titles = ['Eilmeldung: Brücke in Linz gesperrt', 'Eilmeldung: Minister tritt zurück',
                  'Eilmeldung: Erdbeben in Kärnten', 'Eilmeldung: Flughafen Wien geschlossen']
        for i, title in enumerate(titles):
            now = NOW + i * 1000
            c = candidate(title, url=f'https://site{i}.at/a')
            c['published_at'] = now - 60
            state = m.select_updates([c], state, now, 60, 15, s)
        self.assertEqual(len(state['updates']), 2)
        self.assertEqual(list(state['daily'].values()), [2])

    def test_reason_is_recorded(self):
        m = load_short_updates()
        result = m.select_updates([candidate('Eilmeldung: Brücke gesperrt')], {}, NOW, 60, 15, settings())
        self.assertEqual(result['updates'][0]['reason'], 'Stichwort')


class PublicationTests(unittest.TestCase):
    update = {'id': 'a' * 24, 'title': 'Brücke <gesperrt>', 'text': 'Die Brücke ist gesperrt.',
              'created_at': NOW, 'video': 'short-update-video/' + 'a' * 24 + '.mp4', 'video_bytes': 1234}
    feed = ('<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>'
            '<item><title>Nachrichten</title><guid isPermaLink="false">x</guid></item></channel></rss>')

    def test_feed_merge_puts_breaking_first_and_is_idempotent(self):
        once = b.merge_into_feed(self.feed, [self.update], 'https://example.org/')
        twice = b.merge_into_feed(once, [self.update], 'https://example.org/')
        self.assertEqual(once, twice)
        self.assertLess(once.index('Eilmeldung: Brücke &lt;gesperrt&gt;'), once.index('<title>Nachrichten'))
        self.assertIn('url="https://example.org/short-update-video/' + 'a' * 24 + '.mp4" length="1234"', once)
        self.assertEqual(b.merge_into_feed(once, [], 'https://example.org/'), self.feed)

    def test_banner_slot_on_start_page(self):
        page = "<html><a class='logo-link'></a><h1>PNH</h1><main></main></html>"
        once = b.inject_banner(page, 3)
        self.assertEqual(once, b.inject_banner(once, 3))
        self.assertLess(once.index('id="breaking-banner"'), once.index('<h1>'))
        self.assertIn('breaking-banner.js', once)
        self.assertEqual(b.inject_banner(page, 0), page)

    @unittest.skipUnless(shutil.which('node'), 'Node.js needed')
    def test_banner_script_picks_fresh_update(self):
        script = ("const {pick}=require(process.argv[1]);const u=[{id:'a'.repeat(24),title:'alt',created_at:0},"
                  "{id:'b'.repeat(24),title:'neu',created_at:9000},{id:'kaputt',title:'x',created_at:9500}];"
                  "console.log(JSON.stringify([pick(u,10000,1)&&pick(u,10000,1).title,pick(u,30000,1)]))")
        out = subprocess.check_output(['node', '-e', script, str(ROOT / 'docs/breaking-banner.js')], text=True)
        self.assertEqual(json.loads(out), ['neu', None])


def silence(_text, destination, seconds=3):
    with wave.open(str(destination), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b'\0\0' * 16000 * seconds)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg needed')
class AcceptanceTests(unittest.TestCase):
    def run_feed(self, title, plan=False, speech=silence):
        m = load_short_updates()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        docs = root / 'docs'
        docs.mkdir()
        (docs / 'feed.xml').write_text(PublicationTests.feed)
        (docs / 'index.html').write_text('<html><h1>PNH</h1></html>')
        url = 'https://example.org/eil/1'
        news = types.SimpleNamespace(
            CONFIG={'feeds': ['https://example.org/test.rss'], 'short_updates': {'breaking': {'keywords': ['eilmeldung']}}},
            ATOM='{atom}', feed_timestamp=lambda node: 0, BASE='https://example.org/',
            FEED_DATES={url: __import__('time').time() - 60},
            items_from_feed=lambda feed: [(title, 'Ein Zug ist entgleist. Die Strecke ist gesperrt.', url, '')],
            edit_news=lambda t, d, *a: t + '.\n' + d, synthesize=speech)
        with patch.object(m, 'ROOT', root), patch.dict(sys.modules, {'generate': news}):
            if plan:
                m.main(['--plan', str(root / 'plan.json')])
            else:
                m.main([])
        return docs

    def test_testfeed_with_keyword_creates_short_clip(self):
        docs = self.run_feed('Eilmeldung: Zug bei Wels entgleist')
        update = json.loads((docs / 'short-updates.json').read_text())['updates'][0]
        clip = docs / update['video']
        self.assertTrue(clip.is_file())
        duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                                  '-of', 'csv=p=0', str(clip)], text=True))
        self.assertLessEqual(duration, 60.5)
        self.assertIn('Eilmeldung: Eilmeldung: Zug bei Wels entgleist', (docs / 'feed.xml').read_text())
        self.assertIn('id="breaking-banner"', (docs / 'index.html').read_text())

    def test_without_hit_no_media_is_produced(self):
        calls = []
        docs = self.run_feed('Neue Ausstellung im Museum', speech=lambda *a: calls.append(a))
        self.assertEqual(calls, [])
        self.assertFalse(list((docs / 'short-update-video').glob('*')))
        self.assertFalse(list((docs / 'short-update-audio').glob('*')))
        self.assertNotIn('Eilmeldung', (docs / 'feed.xml').read_text())

    def test_plan_reports_media_need(self):
        for title, expected in [('Neue Ausstellung im Museum', 'false'), ('Eilmeldung: Zug entgleist', 'true')]:
            with tempfile.NamedTemporaryFile('r+') as output, patch.dict('os.environ', {'GITHUB_OUTPUT': output.name}):
                docs = self.run_feed(title, plan=True)
                self.assertEqual(Path(output.name).read_text().strip(), 'media=' + expected)
                self.assertFalse((docs / 'short-updates.json').exists())

    def test_long_speech_is_capped_at_sixty_seconds(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from short_update_video import render_short_update
        with tempfile.TemporaryDirectory() as tmp:
            audio, clip = Path(tmp) / 'long.wav', Path(tmp) / 'clip.mp4'
            silence('', audio, seconds=70)
            render_short_update({'title': 'Eilmeldung', 'text': 'Text.', 'created_at': NOW, 'source': 'x'},
                                audio, clip, ROOT, {}, 90)
            duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                                      '-of', 'csv=p=0', str(clip)], text=True))
            self.assertLessEqual(duration, 60.5)


if __name__ == '__main__':
    unittest.main()
