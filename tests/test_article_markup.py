"""Article markup must never be spoken or appear in generated subtitles."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.generate import edit_news, extract_article_text, spoken_prose


class ArticleMarkupTests(unittest.TestCase):
    def test_actual_image_credit_and_emphasis(self):
        article = ('![EPA/TOLGA AKMEN](https://i.ds.at/88n6aw/rs:fill:600:0/plain/lido-images/photo.jpg)\n'
                   'Die goldenen Zwei: **Harry Kane** und **Alexia Putellas** haben gewonnen.')
        self.assertEqual(spoken_prose(article), 'Die goldenen Zwei: Harry Kane und Alexia Putellas haben gewonnen.')

    def test_link_label_survives_nested_url_parentheses(self):
        self.assertEqual(spoken_prose('Laut [ORF](https://example.org/wiki/News_(2026)) ist es so. (Stand heute.)'),
                         'Laut ORF ist es so. (Stand heute.)')

    def test_nested_and_linked_images_are_removed(self):
        self.assertEqual(spoken_prose('Vorher. [![Bild](https://example.org/photo_(1).jpg)](https://example.org) Danach.'),
                         'Vorher. Danach.')

    def test_reference_images_links_and_definitions(self):
        article = '![Bild][foto]\n[ORF][quelle] berichtet. [ORF] ebenso.\n\n[foto]: https://example.org/a.jpg\n[quelle]: https://example.org/news\n[ORF]: https://orf.at\n'
        self.assertEqual(spoken_prose(article), 'ORF berichtet. ORF ebenso.')

    def test_html_code_blocks_and_autolinks(self):
        article = '# Titel\n```python\nprint("nicht sprechen")\n```\n<script>tracking()</script><b>Text</b> &amp; mehr. <https://example.org/abc>'
        self.assertEqual(spoken_prose(article), 'Titel Text & mehr.')

    def test_plain_prose_and_numbers_survive(self):
        text = 'Österreich meldet 3,5 Prozent (Stand: 12 Uhr). A_B bleibt als Kennung erhalten.'
        self.assertEqual(spoken_prose(text), text)

    def test_image_only_extraction_falls_back_to_rss(self):
        article = '![Sehr lange Bildbeschreibung](https://example.org/' + 'x' * 200 + '.jpg)'
        with patch('scripts.generate.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps({'content': article}))):
            self.assertIsNone(extract_article_text('https://example.org/story'))

    def test_clean_before_article_length_limit(self):
        prose = 'Dies ist ein ausführlicher Artikel ohne Medienverweise. ' * 5
        article = '![Bild](https://example.org/' + 'x' * 13000 + '.jpg)\n' + prose
        with patch('scripts.generate.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps({'content': article}))):
            self.assertEqual(extract_article_text('https://example.org/story'), prose.strip())

    def test_all_editorial_styles_clean_rss_fallback(self):
        for style in ('original', 'classic', 'brief'):
            with self.subTest(style=style):
                result = edit_news('**Meldung**', '![Bild](https://example.org/a.jpg) [ORF](https://orf.at) berichtet darüber.', style, 2, 180)
                self.assertEqual(result, 'Meldung.\nORF berichtet darüber.')
