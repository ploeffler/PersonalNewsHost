import copy
import json
import re
import shutil
import tempfile
import wave
from unittest.mock import patch
import unittest
from pathlib import Path

from scripts.article_pages import (article_path, broadcast_stamp, build_article_pages,
                                   clean_summary, slugify)

PUBLISHED = 1795240000.0  # 2026-11-21 05:46:40 UTC


def story(title='Neue Bahnverbindung für Österreich', **extra):
    data = {'title': title,
            'summary': 'Nun zum Bereich Verkehr.\nDie ÖBB eröffnen eine neue Strecke. Sie verkürzt die Fahrzeit.',
            'category': 'Regional', 'section': 'local', 'section_label': 'Österreich',
            'start': 65.4, 'end': 90.0,
            'sources': [{'title': 'Neue Strecke eröffnet', 'url': 'https://orf.at/stories/1/'},
                        {'title': 'Bahn: schneller nach Graz', 'url': 'https://www.derstandard.at/x'}]}
    data.update(extra)
    return data


class ArticlePagesTests(unittest.TestCase):
    def test_slug_and_path_are_stable(self):
        self.assertEqual(slugify('Über 1.200 Drohnen: „Abgewehrt“!'), 'ueber-1-200-drohnen-abgewehrt')
        self.assertEqual(slugify('„“'), 'meldung')
        self.assertEqual(article_path('20261121T054640Z', 0, 'Größe'),
                         'artikel/20261121T054640Z/01-groesse.html')
        self.assertEqual(broadcast_stamp(PUBLISHED), '20261121T054640Z')

    def test_summary_drops_section_announcement_and_stays_short(self):
        self.assertEqual(clean_summary(story()['summary']),
                         'Die ÖBB eröffnen eine neue Strecke. Sie verkürzt die Fahrzeit.')
        long_text = 'Ein Satz mit Inhalt. ' * 100
        short = clean_summary(long_text)
        self.assertLessEqual(len(short), 600)
        self.assertTrue(short.endswith('.'))

    def test_every_story_gets_a_complete_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            stories = [story(), story('Zweite <Meldung>', start=0, sources=[{'title': 'x', 'url': 'javascript:alert(1)'}])]
            paths = build_article_pages(docs, stories, PUBLISHED, 'PersonalNewsHost')
            self.assertEqual(len(paths), 2)
            page = (docs / paths[0]).read_text(encoding='utf-8')
            for expected in ['Neue Bahnverbindung für Österreich', 'Österreich · Regional',
                             '21.11.2026, 06:46 Uhr', 'Die ÖBB eröffnen eine neue Strecke.',
                             "href='https://orf.at/stories/1/'>Zum Originalartikel",
                             'Bahn: schneller nach Graz', '../../broadcasts/20261121T054640Z.mp4#t=65.4',
                             'ab 1:05 ansehen', "name='viewport'"]:
                self.assertIn(expected, page)
            self.assertNotIn('Nun zum Bereich', page)
            second = (docs / paths[1]).read_text(encoding='utf-8')
            self.assertIn('Zweite &lt;Meldung&gt;', second)
            self.assertNotIn('javascript:', second)
            manifest = json.loads((docs / 'articles.json').read_text(encoding='utf-8'))
            self.assertEqual([a['path'] for a in manifest['articles']], paths)

    def test_pages_have_no_external_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            page = (docs / build_article_pages(docs, [story()], PUBLISHED, 'X')[0]).read_text()
            # Only plain hyperlinks may leave the site; nothing is loaded from elsewhere.
            for tag in re.findall(r'<(?:script|img|link|iframe|video|track|source)[^>]*>', page):
                self.assertNotRegex(tag, r'(src|href)=.https?://')
            self.assertNotIn('<script', page)

    def test_old_bulletins_are_pruned_with_the_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            old = build_article_pages(docs, [story()], PUBLISHED - 86400, 'X')[0]
            kept = build_article_pages(docs, [story()], PUBLISHED - 3600, 'X')[0]
            (docs / 'broadcasts.json').write_text(json.dumps({'broadcasts': [
                {'id': broadcast_stamp(PUBLISHED - 3600)}, {'id': broadcast_stamp(PUBLISHED)}]}))
            build_article_pages(docs, [story()], PUBLISHED, 'X')
            self.assertFalse((docs / old).exists())
            self.assertTrue((docs / kept).exists())

    def test_disabled_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(build_article_pages(tmp, [story()], PUBLISHED, 'X', enabled=False), [])
            self.assertEqual(list(Path(tmp).iterdir()), [])


@unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
class ArticlePagesBroadcastTests(unittest.TestCase):
    def test_broadcast_links_reachable_page_and_archived_video(self):
        from scripts import generate
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'docs').mkdir()
            (root / 'assets').mkdir()
            cfg = copy.deepcopy(generate.CONFIG)
            cfg.setdefault('editorial', {})['pipeline'] = {'enabled': False}
            cfg.update({'title': 'Test', 'feeds': ['https://example.org/rss'], 'max_items': 2,
                        'max_description_chars': 60, 'tts_engine': 'espeak',
                        'voice_pitch_semitones': 0, 'station_logo': ''})
            cfg['presenter_settings'] = {
                'name': 'Test', 'portrait': 'assets/missing.png', 'background': 'assets/missing.jpg',
                'scenes': {'intro_mode': 'static', 'intro_static_type': 'color',
                           'intro_static_color': '#13243a', 'intro_seconds': 1, 'outro_seconds': 1}}

            def audio(_text, destination):
                with wave.open(str(destination), 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(bytes(16000 * 2 * 2))
            items = [('Erste Testmeldung', 'Kurzer Text eins.', 'https://example.org/a'),
                     ('Zweite Wetterwarnung', 'Kurzer Text zwei.', 'https://example.net/b')]
            with patch.object(generate, 'ROOT', root), patch.object(generate, 'DOCS', root / 'docs'), \
                    patch.object(generate, 'CONFIG', cfg), patch.object(generate, 'items_from_feed', return_value=items), \
                    patch.object(generate, 'crosscheck_headline', return_value={'status': 'disabled', 'matches': []}), \
                    patch.object(generate, 'synthesize', side_effect=audio):
                generate.main()
            docs = root / 'docs'
            manifest = json.loads((docs / 'articles.json').read_text(encoding='utf-8'))
            self.assertEqual(len(manifest['articles']), 2)
            home = (docs / 'index.html').read_text(encoding='utf-8')
            for article in manifest['articles']:
                page = docs / article['path']
                self.assertTrue(page.is_file())
                self.assertIn(article['path'], home)
                self.assertTrue((docs / article['video']).is_file())
                html = page.read_text(encoding='utf-8')
                self.assertIn(article['title'], html)
                self.assertGreater(article['start'], 0)


if __name__ == '__main__':
    unittest.main()
