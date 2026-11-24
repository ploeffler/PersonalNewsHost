"""Suchindex (T031)."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts import search_index as si

NOW = 1_800_000_000
CONFIG = {'editorial': {'broadcast_sections': {'default': 'general', 'sections': [
    {'id': 'general', 'label': 'Allgemein', 'keywords': []}, {'id': 'economy', 'label': 'Wirtschaft', 'keywords': ['Inflation']}]}}}


def article(i, title, text='Kurztext', url=None):
    return {'title': title, 'text': text, 'url': url or f'https://www.news.example/{i}', 'published_at': NOW - i}


class SearchIndexTests(unittest.TestCase):
    def test_articles_and_broadcasts_are_indexed(self):
        archive = {'broadcasts': [{'id': 'b1', 'show': 'main', 'title': 'Nachrichten 7 Uhr', 'created_at': NOW,
                                   'stories': [{'title': 'Inflation sinkt'}], 'video': 'broadcasts/b1.mp4'}]}
        index = si.build_index(CONFIG, {'articles': [article(1, 'Inflation steigt'), article(2, 'Böse', url='javascript:x')]},
                               archive, {'articles': [{'title': 'Inflation steigt', 'path': 'artikel/x.html'}]}, NOW)
        kinds = {e['k']: e for e in index['entries']}
        self.assertEqual(len(index['entries']), 2)
        self.assertEqual(kinds['a']['section'], 'Wirtschaft')
        self.assertEqual(kinds['a']['url'], 'artikel/x.html')
        self.assertEqual(kinds['a']['source'], 'news.example')
        self.assertEqual(kinds['b']['url'], 'broadcasts/b1.mp4')
        self.assertIn('Inflation sinkt', kinds['b']['text'])

    def test_size_limit_drops_oldest_first(self):
        store = {'articles': [article(i, f'Meldung {i}', text='x ' * 100) for i in range(1, 400)]}
        index = si.build_index(CONFIG, store, {}, {}, NOW, max_bytes=20_000)
        self.assertLessEqual(si._size(index), 20_000)
        self.assertTrue(index['truncated'])
        self.assertEqual(index['entries'][0]['title'], 'Meldung 1')
        self.assertLess(len(index['entries']), 399)

    def test_settings_validation_and_disable(self):
        self.assertEqual(si.settings_from({'search': {'max_bytes': 5}})['max_bytes'], si.DEFAULT_MAX_BYTES)
        self.assertEqual(si.settings_from({'search': {'max_bytes': 50_000}})['max_bytes'], 50_000)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(si.write_index(tmp, {'search': {'enabled': False}}, now=NOW))
            self.assertFalse((Path(tmp) / 'search-index.json').exists())

    def test_write_index_is_idempotent_and_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            si.write_index(tmp, CONFIG, {'articles': [article(1, 'Eins')]}, {}, {}, NOW)
            target = Path(tmp) / 'search-index.json'
            first = target.stat().st_mtime_ns
            si.write_index(tmp, CONFIG, {'articles': [article(1, 'Eins')]}, {}, {}, NOW)
            self.assertEqual(target.stat().st_mtime_ns, first)
            self.assertEqual(json.loads(target.read_text(encoding='utf-8'))['entries'][0]['title'], 'Eins')

    def test_update_homepage_writes_index_and_links_search(self):
        from scripts import homepage
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / 'index.html').write_text('<html><head><title>x</title></head><body><main><h1>X</h1></main></body></html>', encoding='utf-8')
            (docs / 'news-store.json').write_text(json.dumps({'articles': [article(1, 'Inflation steigt')]}), encoding='utf-8')
            homepage.update_homepage(docs, CONFIG, NOW)
            self.assertIn("href='search.html'", (docs / 'index.html').read_text(encoding='utf-8'))
            self.assertIn('Inflation steigt', (docs / 'search-index.json').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
