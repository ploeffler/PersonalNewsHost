"""KI-Kennzeichnung (T050)."""
import tempfile
import unittest
from pathlib import Path

from scripts import ai_disclosure as ai
from scripts import article_pages

STORY = {'title': 'Inflation <sinkt>', 'summary': 'Kurz.', 'category': 'Wirtschaft', 'section_label': 'Wirtschaft',
         'start': 3.0, 'end': 9.0, 'sources': [{'title': 'Quelle', 'url': 'https://news.example/1'}]}


class DisclosureTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.docs = Path(tmp.name)
        (self.docs / 'index.html').write_text(
            "<html><body><main><h1>X</h1><video controls src='latest.mp4'></video><h2>Quellen</h2></main></body></html>", encoding='utf-8')
        self.pages = article_pages.build_article_pages(self.docs, [STORY], 1_800_000_000, 'Test')

    def test_about_page_has_function_limits_and_contact(self):
        ai.update_disclosure(self.docs, {'title': 'Test <S>', 'about': {'correction_contact': 'Korrekturen: <b>x</b>@example.org'}})
        about = (self.docs / ai.ABOUT_PAGE).read_text(encoding='utf-8')
        for heading in ('Funktionsweise', 'Grenzen', 'Korrekturen'):
            self.assertIn(f'<h2>{heading}</h2>', about)
        self.assertIn('Korrekturen: &lt;b&gt;x&lt;/b&gt;@example.org', about)
        self.assertIn('Test &lt;S&gt;', about)
        self.assertIn(ai.LABEL, about)

    def test_default_contact_points_to_imprint(self):
        ai.update_disclosure(self.docs, {})
        self.assertIn("href='impressum.html'>Impressum</a>.</p>", (self.docs / ai.ABOUT_PAGE).read_text(encoding='utf-8'))

    def test_start_page_label_follows_video_and_article_pages_labelled(self):
        self.assertEqual(sorted(ai.missing_disclosure(self.docs)), sorted(['index.html', self.pages[0]]))
        ai.update_disclosure(self.docs, {})
        index = (self.docs / 'index.html').read_text(encoding='utf-8')
        self.assertLess(index.index('</video>'), index.index(ai.START))
        self.assertIn(f"href='{ai.ABOUT_PAGE}'", index)
        article = (self.docs / self.pages[0]).read_text(encoding='utf-8')
        self.assertIn(f"href='../../{ai.ABOUT_PAGE}'", article)
        self.assertIn('Quellen abgerufen für die Sendung vom', article)
        self.assertIn("href='https://news.example/1'", article)
        self.assertEqual(ai.missing_disclosure(self.docs), [])

    def test_idempotent_and_replaced_not_duplicated(self):
        ai.update_disclosure(self.docs, {})
        first = {p: p.read_text(encoding='utf-8') for p in self.docs.rglob('*.html')}
        ai.update_disclosure(self.docs, {})
        self.assertEqual(first, {p: p.read_text(encoding='utf-8') for p in self.docs.rglob('*.html')})
        self.assertEqual((self.docs / 'index.html').read_text(encoding='utf-8').count(ai.START), 1)

    def test_missing_disclosure_detects_unlabelled_page(self):
        ai.update_disclosure(self.docs, {})
        (self.docs / self.pages[0]).write_text('<html><body>nackt</body></html>', encoding='utf-8')
        self.assertEqual(ai.missing_disclosure(self.docs), [self.pages[0]])

    def test_update_homepage_creates_label_and_sitemap_entry(self):
        from scripts import homepage
        homepage.update_homepage(self.docs, {'title': 'T'}, 1_800_000_000)
        self.assertEqual(ai.missing_disclosure(self.docs), [])
        self.assertIn('ueber-diese-sendung.html', (self.docs / 'sitemap.xml').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
