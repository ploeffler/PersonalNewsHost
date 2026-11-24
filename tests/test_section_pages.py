"""Rubrikenseiten und Sendungsseiten (T022)."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts import section_pages as sp

NOW = 1_800_000_000
CONFIG = {'title': 'Test <Sender>', 'editorial': {'broadcast_sections': {
    'default': 'general',
    'sections': [{'id': 'general', 'label': 'Allgemein', 'keywords': []},
                 {'id': 'economy', 'label': 'Wirtschaft', 'keywords': ['Inflation']},
                 {'id': 'local', 'label': 'Lokales', 'keywords': []}],
    'feed_sections': {'https://local.example/rss': 'local'}}},
    'shows': [{'id': 'main', 'title': 'Hauptsendung'}, {'id': 'abend', 'title': 'Abendjournal'}]}


def article(i, title, feed='https://news.example/rss', url=None):
    return {'id': str(i), 'title': title, 'url': url or f'https://www.news.example/{i}',
            'published_at': NOW - i * 60, 'feed_urls': [feed]}


def broadcast(i, show):
    return {'id': f'b{i}', 'show': show, 'title': f'Sendung {i}', 'created_at': NOW - i * 3600,
            'created_utc': '2027-01-01T00:00:00+00:00', 'local_date': '2027-01-01', 'local_time': '07:05',
            'stories': [{'title': 'Story <x>', 'page': None, 'sources': []}], 'video': None}


class SectionPageTests(unittest.TestCase):
    def build(self, articles, broadcasts=(), config=CONFIG):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        docs = Path(tmp.name)
        written = sp.build_section_pages(docs, config, {'articles': articles}, {'broadcasts': list(broadcasts)}, {}, NOW)
        return docs, written

    def test_every_configured_section_and_show_has_a_page(self):
        docs, written = self.build([])
        self.assertEqual(sorted(written), sorted([
            'rubrik/general/index.html', 'rubrik/economy/index.html', 'rubrik/local/index.html',
            'sendung/main/index.html', 'sendung/abend/index.html']))
        for rel in written:
            self.assertTrue((docs / rel).is_file())
        self.assertIn('noch keine Meldungen', (docs / 'rubrik/local/index.html').read_text(encoding='utf-8'))

    def test_assignment_escaping_and_unsafe_links(self):
        docs, _ = self.build([article(1, 'Inflation steigt'), article(2, 'Graz <b>Wahl</b>', feed='https://local.example/rss'),
                              article(3, 'Böse', url='javascript:alert(1)')])
        economy = (docs / 'rubrik/economy/index.html').read_text(encoding='utf-8')
        local = (docs / 'rubrik/local/index.html').read_text(encoding='utf-8')
        self.assertIn('Inflation steigt', economy)
        self.assertNotIn('Graz', economy)
        self.assertIn('Graz &lt;b&gt;Wahl&lt;/b&gt;', local)
        self.assertNotIn('<b>', local)
        self.assertNotIn('Böse', ''.join(p.read_text(encoding='utf-8') for p in docs.rglob('*.html')))

    def test_pagination_and_stale_pages_removed(self):
        many = [article(i, f'Meldung {i}', feed='https://local.example/rss') for i in range(1, 46)]
        docs, _ = self.build(many)
        folder = docs / 'rubrik/local'
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ['index.html', 'page-2.html', 'page-3.html'])
        first = (folder / 'index.html').read_text(encoding='utf-8')
        self.assertIn("rel='next' href='page-2.html'", first)
        self.assertNotIn("rel='prev'", first)
        self.assertIn('Seite 1 von 3', first)
        last = (folder / 'page-3.html').read_text(encoding='utf-8')
        self.assertIn("rel='prev' href='page-2.html'", last)
        self.assertEqual(first.split("<ul class='page-list'>")[1].split('</ul>')[0].count('<li>'), sp.PAGE_SIZE)
        # fewer articles later: page-2/3 disappear
        sp.build_section_pages(docs, CONFIG, {'articles': many[:5]}, {}, {}, NOW)
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ['index.html'])

    def test_breadcrumbs_and_cross_navigation(self):
        docs, _ = self.build([], [broadcast(1, 'main')])
        page = (docs / 'rubrik/economy/index.html').read_text(encoding='utf-8')
        self.assertIn("aria-label='Brotkrumen'", page)
        self.assertIn("<a href='../../index.html'>Start</a>", page)
        self.assertIn("<span aria-current='page'>Wirtschaft</span>", page)
        for target in ('rubrik/general/index.html', 'rubrik/local/index.html', 'sendung/main/index.html', 'sendung/abend/index.html'):
            self.assertIn(f"href='../../{target}'", page)
        self.assertIn("aria-current='page'>Wirtschaft</a>", page)
        show = (docs / 'sendung/main/index.html').read_text(encoding='utf-8')
        self.assertIn("href='../../archive.html'", show)
        self.assertIn('Sendung 1', show)
        self.assertIn('Story &lt;x&gt;', show)
        self.assertNotIn('Sendung 1', (docs / 'sendung/abend/index.html').read_text(encoding='utf-8'))
        self.assertIn('Test &lt;Sender&gt;', page)

    def test_legacy_config_has_main_show(self):
        legacy = {k: v for k, v in CONFIG.items() if k != 'shows'}
        _, written = self.build([], config=legacy)
        self.assertIn('sendung/main/index.html', written)
        self.assertIn('rubrik/general/index.html', written)

    def test_no_sections_configured_falls_back_to_general(self):
        _, written = self.build([article(1, 'Etwas')], config={'title': 'X'})
        self.assertEqual(sorted(written), ['rubrik/general/index.html', 'sendung/main/index.html'])

    def test_unsafe_ids_cannot_escape_folder(self):
        config = {'title': 'X', 'shows': [{'id': '../evil', 'title': 'E'}],
                  'editorial': {'broadcast_sections': {'sections': [{'id': '../../x', 'label': 'X'}]}}}
        docs, written = self.build([], config=config)
        self.assertEqual(written, ['rubrik/x/index.html', 'sendung/evil/index.html'])
        self.assertTrue(all(p.resolve().is_relative_to(docs.resolve()) for p in docs.rglob('*')))

    def test_start_page_links_and_update_homepage_builds_pages(self):
        from scripts import homepage
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / 'index.html').write_text('<html><head><title>x</title></head><body><main><h1>X</h1></main></body></html>', encoding='utf-8')
            (docs / 'news-store.json').write_text(json.dumps({'articles': [article(1, 'Inflation steigt')]}), encoding='utf-8')
            self.assertTrue(homepage.update_homepage(docs, CONFIG, NOW))
            index = (docs / 'index.html').read_text(encoding='utf-8')
            self.assertIn("href='rubrik/economy/index.html'", index)
            self.assertIn("href='sendung/abend/index.html'", index)
            self.assertIn('Inflation steigt', (docs / 'rubrik/economy/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
