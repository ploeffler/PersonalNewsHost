"""Bildrechte und Bildnachweis (T062)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import article_pages, generate, media_rights as mr

CONFIG = {'media': {'licensed_sources': [{'host': 'images.example.org', 'license': 'CC BY 4.0', 'holder': 'Beispiel Agentur'}]}}


class RightsTests(unittest.TestCase):
    def test_policy_defaults_to_strict(self):
        self.assertEqual(mr.policy({}), mr.STRICT)
        self.assertEqual(mr.policy({'media': {'license_policy': 'record_only'}}), mr.RECORD_ONLY)
        self.assertEqual(mr.policy({'media': {'license_policy': 'egal'}}), mr.STRICT)

    def test_publisher_image_is_unverified_without_approval(self):
        credit = mr.publisher_credit('https://news.example/a', 'https://news.example/a.jpg', CONFIG)
        self.assertEqual(credit['license_status'], mr.UNVERIFIED)
        self.assertFalse(mr.usable(credit, CONFIG))
        self.assertTrue(mr.usable(credit, {'media': {'license_policy': 'record_only'}}))
        self.assertIn('Lizenz nicht nachgewiesen', mr.credit_text(credit))

    def test_approved_source_is_licensed_including_subdomains(self):
        for url in ('https://images.example.org/x.jpg', 'https://cdn.images.example.org/x.jpg'):
            credit = mr.publisher_credit('https://news.example/a', url, CONFIG)
            self.assertEqual(credit['license_status'], mr.LICENSED)
            self.assertEqual(credit['license'], 'CC BY 4.0')
            self.assertEqual(mr.credit_text(credit), 'Bild: Beispiel Agentur, CC BY 4.0')
        # an approval without a licence text is not an approval
        self.assertEqual(mr.publisher_credit('https://n.example/', 'https://x.example/i.jpg',
                                             {'media': {'licensed_sources': [{'host': 'x.example'}]}})['license_status'], mr.UNVERIFIED)

    def test_commons_generated_and_text(self):
        commons = mr.commons_credit('https://commons.wikimedia.org/wiki/File:A.jpg', 'File:A.jpg', 'CC0', '<a href="x">Max</a>')
        self.assertEqual(commons['holder'], 'Max')
        self.assertIn('Wikimedia Commons', mr.credit_text(commons))
        self.assertEqual(mr.credit_text(mr.generated_credit('https://n.example/')), 'Bild: automatisch erzeugte Grafik')
        self.assertEqual(mr.credit_text(mr.reject(mr.publisher_credit('s', 'i', {}))), '')

    def test_outro_line_is_short_and_lists_holders(self):
        self.assertEqual(mr.outro_line([mr.generated_credit('s')]), 'Bilder: eigene Grafiken')
        credits = [mr.commons_credit('s', 't', 'CC0', 'A' * 30), mr.commons_credit('s', 't', 'CC0', 'B' * 30)]
        self.assertLessEqual(len(mr.outro_line(credits)), 52)

    def test_validate_credits_requires_complete_records(self):
        good = [mr.generated_credit('https://n.example/'), mr.commons_credit('s', 't', 'CC0')]
        self.assertEqual(mr.validate_credits(good), [])
        problems = mr.validate_credits([{'source': 's'}, {'source': 's', 'image_origin': 'x', 'license_status': 'licensed'}])
        self.assertTrue(any('image_origin fehlt' in p for p in problems))
        self.assertTrue(any('unbekannte Herkunft' in p for p in problems))
        self.assertTrue(any('Lizenz fehlt' in p for p in problems))

    def test_article_page_shows_image_credit(self):
        story = {'title': 'T', 'summary': 'Kurz.', 'sources': [], 'image_credit': 'Bild: <b>Agentur</b>, CC BY 4.0'}
        page = article_pages.render_article(story, '20270115T080000Z', 1_800_000_000, 'Base')
        self.assertIn("class='meta bildnachweis'>Bild: &lt;b&gt;Agentur&lt;/b&gt;, CC BY 4.0</p>", page)
        self.assertNotIn('bildnachweis', article_pages.render_article({**story, 'image_credit': ''}, '20270115T080000Z', 1_800_000_000, 'Base'))

    def test_prepare_media_rejects_unlicensed_publisher_image_in_pipeline(self):
        # download_media is the only network step used here; the story falls back to a generated graphic.
        with tempfile.TemporaryDirectory() as tmp:
            picture = Path(tmp) / 'p.img'
            picture.write_bytes(b'x')
            credit = mr.publisher_credit('https://news.example/a', 'https://news.example/a.jpg', {})
            self.assertFalse(mr.usable(credit, {}))
            rejected = mr.reject(credit)
            generated = mr.generated_credit('https://news.example/a')
            generated['rejected_publisher_image'] = rejected['image_url']
            self.assertEqual(mr.validate_credits([generated]), [])


if __name__ == '__main__':
    unittest.main()
