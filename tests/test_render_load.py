"""Offline production-layout regression; set PNH_RENDER_SECONDS=155 for a full-length benchmark."""
import copy
import json
import importlib.util
import math
import struct
import threading
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
            config.setdefault("editorial", {})["pipeline"] = {"enabled": False}
            config.update(max_items=5, feeds=['https://example.org/rss'])
            config['production'] = {'parallel_workers': 2}
            config['editorial'] = {'crosscheck': {'enabled': False}, 'topic_clustering': {'enabled': False}, 'pipeline': {'enabled': False}}
            config['media'] = {'mode': 'images', 'web_image_fallback': False, 'enhancement': 'off'}
            config['presenter_settings']['lip_sync'] = {'enabled': True, 'fps': 20}
            entries = [(f'Meldung {i}', 'Dies ist eine lokale Testmeldung.', f'https://example.org/{i}', []) for i in range(5)]
            # Eight segments: two intro parts, five stories and the outro.
            # Pair each task with another worker, proving actual TTS overlap.
            speech_barrier = threading.Barrier(2, timeout=5)
            def speech(text, destination):
                speech_barrier.wait()
                index = int(destination.stem.split('_')[-1])
                with wave.open(str(destination), 'wb') as audio:
                    audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(struct.pack('<h', index + 1) * round(seconds / 8 * 16000))
            def frames(_portrait, audio, directory, fps, mouth):
                with wave.open(str(audio), 'rb') as wav:
                    count = math.ceil(wav.getnframes() / wav.getframerate() * fps)
                    speech_frames = round(seconds / 8 * 16000)
                    pause_frames = round(1.2 * 16000)
                    for index in range(8):
                        self.assertEqual(wav.readframes(speech_frames),
                                         struct.pack('<h', index + 1) * speech_frames)
                        if 1 <= index < 7:
                            self.assertEqual(wav.readframes(pause_frames), bytes(pause_frames * 2))
                    self.assertEqual(wav.readframes(1), b'')
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
            timeline = json.loads((docs / 'timeline.json').read_text())
            self.assertEqual([part['story_index'] for part in timeline['segments'][2:-1]], list(range(5)))
            credits = json.loads((docs / 'media-credits.json').read_text())
            self.assertEqual([credit['source'] for credit in credits], [entry[2] for entry in entries])
            command = next(args for args in commands if '-filter_complex' in args)
            graph = command[command.index('-filter_complex') + 1]
            self.assertNotIn('split=5', graph)
            self.assertEqual(graph.count('scale=610:765:'), 1)
            self.assertIn('[withpresenter]', graph)
            self.assertEqual(graph.count('pad=620:384:'), 5)
            for idx in range(5):
                self.assertIn(f'intro_topic_{idx}.txt', graph)
                self.assertIn(f'[introtopic{idx}]', graph)
            metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(docs / 'latest.mp4')], text=True))
            streams = metadata['streams']
            self.assertTrue(any(s['codec_type'] == 'audio' for s in streams))
            video = next(s for s in streams if s['codec_type'] == 'video')
            self.assertEqual((video['width'], video['height']), (1280, 720))
            self.assertAlmostEqual(float(metadata['format']['duration']), seconds + 6 * 1.2, delta=0.2)
            # Inspect the actual rendered intro: five successive topic cards
            # must produce five distinct images, not a static list or overlap.
            intro_duration = seconds / 4 + 1.2
            cards = []
            for idx in range(5):
                cards.append(subprocess.check_output([
                    'ffmpeg', '-v', 'error', '-ss', str(intro_duration * (idx + 0.5) / 5),
                    '-i', str(docs / 'latest.mp4'), '-vf', 'crop=1040:160:120:470',
                    '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']))
            self.assertEqual(len(set(cards)), 5)
            self.assertTrue((docs / 'subtitles.de.vtt').read_text().startswith('WEBVTT'))
            print(f'Production layout: {seconds:.1f}s video rendered in {elapsed:.2f}s')
