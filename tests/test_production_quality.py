"""Quality gate failures preserve the complete last successful edition."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import generate
from scripts.production_quality import check_edition, QualityError, staged_edition


class ProductionQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.destination = self.root / 'docs'
        self.destination.mkdir()
        self.groups = [{'headline': 'Public headline', 'sources': [{'url': 'https://fixture.example/a'}]}]
        self.timeline = {'duration': 2, 'segments': [{'type': 'story', 'start': 0, 'end': 2}]}
        self.media = {'format': {'duration': '2'}, 'streams': [{'codec_type': 'video'}, {'codec_type': 'audio'}]}

    def fixture(self, folder):
        (folder / 'latest.mp4').write_bytes(b'new video')
        (folder / 'feed.xml').write_text('new feed')
        (folder / 'index.html').write_text('new page')
        (folder / 'story-groups.json').write_text(json.dumps(self.groups))
        (folder / 'timeline.json').write_text(json.dumps(self.timeline))
        (folder / 'transcript.txt').write_text('Public transcript')

    def probe(self):
        return patch('scripts.production_quality.subprocess.run', return_value=type('Probe', (), {'stdout': json.dumps(self.media)})())

    def test_valid_edition_is_accepted(self):
        self.fixture(self.destination)
        with self.probe():
            self.assertEqual(check_edition(self.destination, {})['stories'], 1)

    def test_missing_audio_video_wrong_duration_and_empty_sections_rejected(self):
        cases = ['audio', 'video', 'duration', 'gap', 'empty', 'sources', 'minimum', 'transcript']
        for case in cases:
            with self.subTest(case=case):
                self.media = {'format': {'duration': '2'}, 'streams': [{'codec_type': 'video'}, {'codec_type': 'audio'}]}
                self.timeline = {'duration': 2, 'segments': [{'type': 'story', 'start': 0, 'end': 2}]}
                self.groups = [{'headline': 'Title', 'sources': [{'url': 'https://fixture.example/a'}]}]
                config = {}
                if case in ('audio', 'video'):self.media['streams'] = [s for s in self.media['streams'] if s['codec_type'] != case]
                if case == 'duration':self.media['format']['duration'] = '20'
                if case == 'gap':self.timeline['segments'][0]['start'] = 1
                if case == 'empty':self.timeline['segments'][0]['end'] = 0
                if case == 'sources':self.groups[0]['sources'] = []
                if case == 'minimum':config = {'quality': {'min_items': 2}}
                self.fixture(self.destination)
                if case == 'transcript':(self.destination / 'transcript.txt').write_text(' ')
                with self.probe(), self.assertRaises(QualityError):check_edition(self.destination, config)

    def test_failed_render_or_gate_keeps_previous_video_feed_and_page(self):
        old = {'latest.mp4': b'old video', 'feed.xml': b'old feed', 'index.html': b'old page'}
        for name, content in old.items():(self.destination / name).write_bytes(content)
        for failure in ('render', 'quality'):
            with self.subTest(failure=failure):
                def attempt():
                    self.fixture(generate.DOCS)
                    if failure == 'render':raise RuntimeError('simulated renderer failure')
                with patch.object(generate, 'DOCS', self.destination), patch.object(generate, '_generate', side_effect=attempt), patch('scripts.production_quality.check_edition', side_effect=QualityError('Missing audio stream')):
                    with self.assertRaises(RuntimeError):generate.main()
                    self.assertEqual(generate.DOCS, self.destination)
                for name, content in old.items():self.assertEqual((self.destination / name).read_bytes(), content)
                self.assertEqual(list(self.root.glob('.pnh-edition-*')), [])

    def test_success_replaces_complete_edition_and_preserves_static_assets(self):
        (self.destination / 'site.css').write_text('static asset')
        with staged_edition(self.destination) as candidate:self.fixture(candidate)
        self.assertEqual((self.destination / 'latest.mp4').read_bytes(), b'new video')
        self.assertEqual((self.destination / 'feed.xml').read_text(), 'new feed')
        self.assertEqual((self.destination / 'site.css').read_text(), 'static asset')

    def test_failed_final_rename_restores_previous_directory(self):
        import os
        original = os.replace
        (self.destination / 'latest.mp4').write_bytes(b'old video')
        def replace(source, target):
            if Path(source).name == 'candidate':raise OSError('simulated rename failure')
            return original(source, target)
        with patch('scripts.production_quality.os.replace', side_effect=replace), self.assertRaises(OSError):
            with staged_edition(self.destination) as candidate:self.fixture(candidate)
        self.assertEqual((self.destination / 'latest.mp4').read_bytes(), b'old video')

    def test_old_media_cannot_satisfy_new_edition_contract(self):
        self.fixture(self.destination)
        with self.assertRaises(QualityError):
            with staged_edition(self.destination) as candidate:check_edition(candidate, {})
        self.assertEqual((self.destination / 'latest.mp4').read_bytes(), b'new video')
