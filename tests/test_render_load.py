"""Offline production-layout regression; set PNH_RENDER_SECONDS=155 for a full-length benchmark."""
import copy
import json
import importlib.util
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from scripts import generate


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe') and importlib.util.find_spec('PIL'), 'FFmpeg and Pillow required')
class ProductionRenderTests(unittest.TestCase):
    def test_five_stories_with_animated_presenter_and_media(self):
        from PIL import Image
        seconds = float(os.environ.get('PNH_RENDER_SECONDS', '6'))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / 'docs'
            docs.mkdir()
            assets = root / 'assets'
            assets.mkdir()
            for name in ('background.jpg', 'host.png', 'desk_foreground.png'):
                shutil.copyfile(generate.ROOT / 'assets' / name, assets / name)
            picture = assets / 'news.png'
            Image.new('RGB', (620, 384), '#286090').save(picture)
            portrait = assets / 'animated.png'
            with Image.open(assets / 'host.png') as image:
                image.thumbnail((530, 665))
                image.save(portrait)
            config = copy.deepcopy(generate.CONFIG)
            config.update(max_items=5, feeds=['https://example.org/rss'])
            config['editorial'] = {'crosscheck': {'enabled': False}, 'topic_clustering': {'enabled': False}}
            config['media'] = {'mode': 'images', 'web_image_fallback': False, 'enhancement': 'off'}
            config['presenter_settings']['lip_sync'] = {'enabled': True, 'fps': 20}
            entries = [(f'Meldung {i}', 'Dies ist eine lokale Testmeldung.', f'https://example.org/{i}', []) for i in range(5)]
            def speech(text, destination):
                with wave.open(str(destination), 'wb') as audio:
                    audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(bytes(round(seconds / 8 * 16000) * 2))
            def frames(_portrait, audio, directory, fps, mouth):
                with wave.open(str(audio), 'rb') as wav:
                    count = math.ceil(wav.getnframes() / wav.getframerate() * fps)
                directory.mkdir()
                # Decode the same realistic PNG sequence without spending benchmark
                # time generating thousands of mouth deformations.
                for i in range(count):
                    (directory / f'lip_{i:06d}.png').symlink_to(portrait)
                return count
            commands = []
            original_run = generate.run
            def run(args):
                commands.append(args)
                return original_run(args)
            started = time.monotonic()
            with patch.object(generate, 'ROOT', root), patch.object(generate, 'DOCS', docs), patch.object(generate, 'CONFIG', config), patch.object(generate, 'items_from_feed', return_value=entries), patch.object(generate, 'synthesize', side_effect=speech), patch.object(generate, 'extract_article_text', return_value=None), patch.object(generate, 'article_image_candidates', return_value=[]), patch.object(generate, 'download_media', return_value=(picture, 'image')), patch.object(generate, 'run', side_effect=run), patch.dict(sys.modules, {'lipsync': types.SimpleNamespace(generate_frames=frames)}):
                generate.main()
            elapsed = time.monotonic() - started
            command = next(args for args in commands if '-filter_complex' in args)
            graph = command[command.index('-filter_complex') + 1]
            self.assertNotIn('split=5', graph)
            self.assertEqual(graph.count('scale=610:765:'), 1)
            self.assertIn('[withpresenter]', graph)
            self.assertEqual(graph.count('pad=620:384:'), 5)
            metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(docs / 'latest.mp4')], text=True))
            streams = metadata['streams']
            self.assertTrue(any(s['codec_type'] == 'audio' for s in streams))
            video = next(s for s in streams if s['codec_type'] == 'video')
            self.assertEqual((video['width'], video['height']), (1280, 720))
            self.assertAlmostEqual(float(metadata['format']['duration']), seconds, delta=0.2)
            self.assertTrue((docs / 'subtitles.de.vtt').read_text().startswith('WEBVTT'))
            print(f'Production layout: {seconds:.1f}s video rendered in {elapsed:.2f}s')
