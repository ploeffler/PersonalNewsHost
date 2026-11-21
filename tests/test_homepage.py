"""Start page in editorial layout (T021)."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts import homepage as hp

NOW = 1_800_000_000
CONFIG = {'editorial': {'broadcast_sections': {
    'default': 'general',
    'sections': [{'id': 'general', 'label': 'Allgemein', 'keywords': []},
                 {'id': 'economy', 'label': 'Wirtschaft', 'keywords': ['Inflation', 'Börse']},
                 {'id': 'local', 'label': 'Lokales', 'keywords': []}],
    'feed_sections': {'https://local.example/rss': 'local'}}}}


def article(i, title, feed='https://news.example/rss', age=600, url=None):
    return {'id': str(i), 'title': title, 'url': url or f'https://www.news.example/{i}',
            'published_at': NOW - age, 'feed_urls': [feed]}


STORE = {'articles': [
    article(1, 'Inflation sinkt im November', age=100),
    article(2, 'Neuer Bürgermeister in Graz', feed='https://local.example/rss', age=200),
    article(3, 'Regierung plant <Reform>', age=300),
    article(4, 'Börse schließt im Plus', age=400),
    article(5, 'Alte Meldung', age=90000),
    article(6, 'Ohne Link', url='javascript:alert(1)'),
    article(7, 'Lokales Wetter', feed='https://local.example/rss', age=500)]}
PAGE = ("<!doctype html><html lang='de'><style>body{}</style><h1>PNH</h1>"
        "<main class='broadcast-layout'></main><section id=\"news-overview\"></section></html>")


class RenderTests(unittest.TestCase):
    def blocks(self, manifest=None):
        return hp.render_blocks(STORE, CONFIG, manifest, NOW)

    def test_sections_and_newest_posts(self):
        html = self.blocks()
        headings = re.findall(r"<h3 id='rubrik-[^']+'>([^<]+)</h3>", html)
        self.assertEqual(headings, ['Allgemein', 'Wirtschaft', 'Lokales'])
        economy = html.split('Wirtschaft</h3>')[1].split('</section>')[0]
        self.assertIn('Inflation sinkt', economy)
        self.assertIn('Börse schließt', economy)
        local = html.split('Lokales</h3>')[1].split('</section>')[0]
        self.assertIn('Neuer Bürgermeister', local)
        latest = html.split("<ol class='latest-list'>")[1].split('</ol>')[0]
        self.assertEqual(re.findall(r">([^<]+)</a>", latest)[:2], ['Inflation sinkt im November', 'Neuer Bürgermeister in Graz'])

    def test_old_unsafe_and_markup_are_handled(self):
        html = self.blocks()
        self.assertNotIn('Alte Meldung', html)
        self.assertNotIn('Ohne Link', html)
        self.assertNotIn('javascript:', html)
        self.assertIn('Regierung plant &lt;Reform&gt;', html)
        self.assertIn("rel='noopener noreferrer'", html)
        self.assertIn('news.example', html)
        self.assertNotIn('www.news.example ·', html)

    def test_broadcast_stories_link_to_article_pages(self):
        html = self.blocks({'articles': [{'title': 'Inflation sinkt im November', 'path': 'artikel/X/01-inflation.html'}]})
        self.assertIn("<a href='artikel/X/01-inflation.html'>Inflation sinkt im November</a>", html)

    def test_empty_store(self):
        html = hp.render_blocks({}, {}, None, NOW)
        self.assertIn('keine Meldungen', html)
        self.assertIn('Noch keine Beiträge', html)


class PlacementTests(unittest.TestCase):
    def test_inserted_before_news_list_and_replaced_in_place(self):
        once = hp.place_blocks(PAGE, hp.render_blocks(STORE, CONFIG, None, NOW))
        self.assertLess(once.index(hp.START), once.index('<section id="news-overview"'))
        self.assertGreater(once.index(hp.START), once.index('</main>'))
        newer = hp.render_blocks({'articles': [article(9, 'Ganz neu', age=10)]}, CONFIG, None, NOW)
        twice = hp.place_blocks(once, newer)
        self.assertEqual(twice.count(hp.START), 1)
        self.assertIn('Ganz neu', twice)
        self.assertNotIn('Inflation sinkt', twice)
        self.assertEqual(twice.count('site.css'), 1)
        self.assertEqual(twice.count('theme.js'), 1)
        self.assertEqual(twice.count('id=\'theme-toggle\''), 1)
        self.assertLess(twice.index('site.css'), twice.index('<h1>'))

    def test_update_homepage_from_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            self.assertFalse(hp.update_homepage(docs, CONFIG, NOW))
            (docs / 'index.html').write_text(PAGE)
            (docs / 'news-store.json').write_text(json.dumps(STORE))
            self.assertTrue(hp.update_homepage(docs, CONFIG, NOW))
            page = (docs / 'index.html').read_text()
            self.assertIn("id='ressorts'", page)
            self.assertIn('id="breaking-banner"', page)
            self.assertLess(page.index('id="breaking-banner"'), page.index('<h1>'))


class StyleTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1] / 'docs'

    def test_light_and_dark_variables_cover_component_styles(self):
        site = (self.root / 'site.css').read_text()
        light = set(re.findall(r'(--[a-z0-9-]+):', site.split('}')[0]))
        dark = set(re.findall(r'(--[a-z0-9-]+):', site.split(':root[data-theme=dark]{')[1].split('}')[0]))
        self.assertEqual(light, dark)
        for name in ('playlist.css', 'news-list.css'):
            css = (self.root / name).read_text()
            self.assertEqual(re.findall(r'#[0-9a-fA-F]{3,8}\b', css), [], name)
            self.assertLessEqual(set(re.findall(r'var\((--[a-z0-9-]+)\)', css)), light, name)
        self.assertIn('prefers-color-scheme:dark', site)


if __name__ == '__main__':
    unittest.main()
