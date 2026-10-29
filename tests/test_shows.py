"""Show resolution and production boundaries, including legacy and failure behavior."""
import copy
import json
from pathlib import Path
import tempfile
import shutil
import wave
import unittest
from unittest.mock import patch

from scripts import generate
from scripts.shows import resolve_shows
from scripts.produce_show import produce
from scripts.validate_config import validate_config

ROOT = Path(__file__).resolve().parents[1]


class ShowTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'config.example.json').read_text())

    def test_legacy_main_is_exact_copy(self):
        resolved = resolve_shows(self.config)
        self.assertEqual(resolved[0]['id'], 'main')
        self.assertEqual(resolved[0]['config'], self.config)
        resolved[0]['config']['feeds'].append('https://changed.example/rss')
        self.assertNotIn('https://changed.example/rss', self.config['feeds'])

    def test_independent_inheritance(self):
        self.config['shows'] = [
            {'id': 'one', 'presenter_settings': {'scenes': {'intro_mode': 'static'}}},
            {'id': 'two', 'feeds': ['https://two.example/rss'], 'schedule': {'timezone': 'Europe/Vienna'}},
        ]
        first, second = resolve_shows(self.config)
        self.assertEqual(first['config']['presenter_settings']['scenes']['intro_mode'], 'static')
        self.assertEqual(second['config']['presenter_settings']['scenes']['intro_mode'], 'avatar')
        self.assertEqual(second['config']['automation']['timezone'], 'Europe/Vienna')
        self.assertEqual(first['config']['feeds'], self.config['feeds'])
        self.assertIn('intro_text', first['config']['presenter_settings']['scenes'])

    def test_ids_and_unknown_fields_rejected(self):
        for shows in ([], [{'id': '../outside'}], [{'id': 'same'}, {'id': 'same'}],
                      [{'id': 'ok', 'max_items': 0}], [{'id': 'ok', 'schedule': {'timezone': 'invalid'}}],
                      [{'id': 'ok', 'feedz': []}]):
            with self.subTest(shows=shows), self.assertRaises(ValueError):
                validate_config(dict(self.config, shows=shows))

    def test_two_productions_restore_globals_and_separate_artifacts(self):
        self.config['shows'] = [{'id': 'one', 'title': 'One'}, {'id': 'two', 'title': 'Two'}]
        initial = generate.CONFIG, generate.DOCS, generate.BASE, copy.deepcopy(generate.FEED_DATES)
        def render():
            (generate.DOCS / 'transcript.txt').write_text(generate.CONFIG['title'])
            self.assertEqual(generate.BASE, './')
            generate.FEED_DATES['temporary'] = 123
        with tempfile.TemporaryDirectory() as tmp, patch.object(generate, 'main', side_effect=render):
            for ident in ('one', 'two'):
                produce(self.config, ident, tmp)
            self.assertEqual((Path(tmp) / 'one/transcript.txt').read_text(), 'One')
            self.assertEqual((Path(tmp) / 'two/transcript.txt').read_text(), 'Two')
            self.assertFalse(json.loads((Path(tmp) / 'two/show.json').read_text())['publication_requested'])
        self.assertIs(generate.CONFIG, initial[0])
        self.assertEqual((generate.DOCS, generate.BASE, generate.FEED_DATES), initial[1:])

    def test_error_restores_context_and_does_not_mark_success(self):
        old = generate.CONFIG, generate.DOCS
        with tempfile.TemporaryDirectory() as tmp, patch.object(generate, 'main', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError): produce(self.config, 'main', tmp)
            self.assertFalse((Path(tmp) / 'main/show.json').exists())
        self.assertIs(generate.CONFIG, old[0])
        self.assertEqual(generate.DOCS, old[1])

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'out'
            root.mkdir()
            (root / 'main').symlink_to(Path(tmp))
            with self.assertRaises(ValueError): produce(self.config, 'main', root)

    def test_unknown_show_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'not-created'
            with self.assertRaises(ValueError): produce(self.config, 'missing', out)
            self.assertFalse(out.exists())

    def test_legacy_entrypoint_does_not_ignore_explicit_shows(self):
        config = dict(self.config, shows=[{'id': 'one'}])
        with patch.object(generate, 'CONFIG', config), patch.object(generate, 'items_from_feed') as fetch:
            with self.assertRaisesRegex(ValueError, 'produce_show'):
                generate.main()
            fetch.assert_not_called()

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_two_shows_generate_separate_videos(self):
        config = copy.deepcopy(self.config)
        config.update(feeds=['https://example.org/rss'], max_items=1)
        config['editorial'] = {'pipeline': {'enabled': False}, 'crosscheck': {'enabled': False}}
        config['media'] = {'mode': 'off', 'web_image_fallback': False, 'enhancement': 'off'}
        config['article_enrichment'] = {'enabled': False}
        config['presenter_settings'] = {'scenes': {'intro_mode': 'static', 'show_headlines': False},
                                        'portrait': 'assets/missing.png', 'background': 'assets/missing.jpg'}
        config['shows'] = [{'id': 'one', 'title': 'First Show'}, {'id': 'two', 'title': 'Second Show'}]
        def audio(_text, destination):
            with wave.open(str(destination), 'wb') as wav:
                wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(32000))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'assets').mkdir()
            with patch.object(generate, 'ROOT', root), \
                 patch.object(generate, 'items_from_feed', return_value=[('Fixture report', 'Source text.', 'https://example.org/story', [])]), \
                 patch.object(generate, 'extract_article_text', return_value='Source text.'), \
                 patch.object(generate, 'synthesize', side_effect=audio):
                for ident in ('one', 'two'):
                    output = produce(config, ident, root / 'out')
                    self.assertGreater((output / 'latest.mp4').stat().st_size, 1000)
                    self.assertTrue((output / 'feed.xml').is_file())
            self.assertIn('First Show', (root / 'out/one/transcript.txt').read_text())
            self.assertIn('Second Show', (root / 'out/two/transcript.txt').read_text())
            self.assertFalse((root / 'docs').exists())

    def test_example_is_valid(self):
        validate_config(json.loads((ROOT / 'config.shows.example.json').read_text()))


if __name__ == '__main__':
    unittest.main()
