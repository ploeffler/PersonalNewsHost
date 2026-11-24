"""Sitemap, robots.txt und Seitenmetadaten (T032)."""
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts import site_meta as sm

BASE = 'https://example.org/news/'
CONFIG = {'title': 'Test <Sender>', 'site': {'base_url': BASE}}
HEAD = "<!doctype html><html lang='de'><head><meta charset='utf-8'><title>{t}</title>{extra}</head><body><h1>{t}</h1><p>Text.</p></body></html>"


def make_site(docs):
    def put(rel, title, extra=''):
        path = docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEAD.format(t=title, extra=extra), encoding='utf-8')
    put('index.html', 'Startseite')
    put('archive.html', 'Archiv')
    put('search.html', 'Suche')
    put('settings.html', 'Konfiguration')
    put('rubrik/economy/index.html', 'Wirtschaft')
    put('rubrik/economy/page-2.html', 'Wirtschaft')
    put('sendung/main/index.html', 'Hauptsendung')
    put('artikel/20261028T130428Z/01-inflation-sinkt.html', 'Inflation &lt;sinkt&gt; – Test',
        "<meta name='description' content='Kurzer Text &amp; mehr'>")


class SiteMetaTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.docs = Path(tmp.name)
        make_site(self.docs)

    def test_sitemap_contains_article_section_and_show_pages(self):
        sm.update_site_meta(self.docs, CONFIG)
        tree = ET.fromstring((self.docs / 'sitemap.xml').read_text(encoding='utf-8'))
        locs = {e.text for e in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
        self.assertEqual(locs, {BASE, BASE + 'archive.html', BASE + 'search.html',
                                BASE + 'rubrik/economy/index.html', BASE + 'rubrik/economy/page-2.html',
                                BASE + 'sendung/main/index.html',
                                BASE + 'artikel/20261028T130428Z/01-inflation-sinkt.html'})
        robots = (self.docs / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn(f'Sitemap: {BASE}sitemap.xml', robots)
        self.assertIn('Allow: /', robots)

    def test_open_graph_twitter_and_canonical(self):
        sm.update_site_meta(self.docs, CONFIG)
        page = (self.docs / 'rubrik/economy/index.html').read_text(encoding='utf-8')
        self.assertIn(f'<link rel="canonical" href="{BASE}rubrik/economy/index.html">', page)
        self.assertIn('<meta property="og:title" content="Wirtschaft">', page)
        self.assertIn('<meta name="twitter:card" content="summary">', page)
        self.assertIn('"@type": "CollectionPage"', page)
        self.assertEqual(page.count(sm.START), 1)

    def test_article_has_newsarticle_data_and_escaping(self):
        sm.update_site_meta(self.docs, CONFIG)
        page = (self.docs / 'artikel/20261028T130428Z/01-inflation-sinkt.html').read_text(encoding='utf-8')
        ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
        data = json.loads(ld)
        self.assertEqual(data['@type'], 'NewsArticle')
        self.assertEqual(data['datePublished'], '2026-10-28T13:04:28+00:00')
        self.assertEqual(data['description'], 'Kurzer Text & mehr')
        block = page.split(sm.START)[1].split(sm.END)[0]
        self.assertNotIn('<sinkt>', block)
        self.assertEqual(data['headline'], 'Inflation <sinkt>')
        self.assertNotIn('<', ld)
        self.assertIn('og:type" content="article"', page)

    def test_start_page_video_object_and_idempotence(self):
        (self.docs / 'broadcasts.json').write_text(json.dumps({'broadcasts': [
            {'id': 'a', 'title': 'Nachrichten', 'created_at': 1_800_000_000, 'video': 'broadcasts/a.mp4'}]}), encoding='utf-8')
        sm.update_site_meta(self.docs, CONFIG)
        index = (self.docs / 'index.html').read_text(encoding='utf-8')
        self.assertIn('"@type": "VideoObject"', index)
        self.assertIn(f'"contentUrl": "{BASE}broadcasts/a.mp4"', index)
        before = {p: p.read_text(encoding='utf-8') for p in self.docs.rglob('*') if p.is_file()}
        sm.update_site_meta(self.docs, CONFIG)
        after = {p: p.read_text(encoding='utf-8') for p in self.docs.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_unlisted_pages_untouched_and_base_url_validation(self):
        sm.update_site_meta(self.docs, CONFIG)
        self.assertNotIn(sm.START, (self.docs / 'settings.html').read_text(encoding='utf-8'))
        self.assertEqual(sm.base_url({'site': {'base_url': 'javascript:alert(1)'}}, env={}), sm.DEFAULT_BASE)
        self.assertEqual(sm.base_url({}, env={'PNH_BASE_URL': 'https://x.example'}), 'https://x.example/')

    def test_update_homepage_writes_sitemap(self):
        from scripts import homepage
        homepage.update_homepage(self.docs, CONFIG, 1_800_000_000)
        self.assertTrue((self.docs / 'sitemap.xml').is_file())
        self.assertIn('og:title', (self.docs / 'index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
