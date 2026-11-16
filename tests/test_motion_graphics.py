import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from scripts.motion_graphics import add_news_card, fit_lines

ROOT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


class MotionGraphicsTests(unittest.TestCase):
    def test_long_text_stays_inside_card(self):
        draw = ImageDraw.Draw(Image.new('RGB', (635, 200)))
        font = ImageFont.truetype(FONT, 28)
        for text in ['W' * 500, 'Änderungen in Österreich: ' * 30]:
            lines = fit_lines(draw, text, font, 587, 3)
            self.assertEqual(len(lines), 3)
            self.assertTrue(lines[-1].endswith('…'))
            self.assertTrue(all(draw.textlength(line, font=font) <= 587 for line in lines))

    def test_render_is_visible_only_during_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = ['ffmpeg', '-v', 'error', '-y', '-filter_complex_threads', '1',
                    '-f', 'lavfi', '-i', 'color=black:s=1280x720:r=20:d=2']
            filters = []
            current = add_news_card(args, filters, '0:v', ROOT, tmp, 0,
                                    'Neue Bahnverbindung für Österreich', 'example.org',
                                    'Verkehr', .25, 1.5, True, FONT)
            args += ['-filter_complex', ';'.join(filters), '-map', f'[{current}]',
                     '-t', '2', '-threads', '1', str(Path(tmp) / 'frame-%02d.png')]
            subprocess.run(args, check=True, capture_output=True)
            def pixel(frame):
                with Image.open(Path(tmp) / f'frame-{frame:02d}.png') as image:
                    return sum(image.getpixel((57, 440))[:3])
            self.assertEqual(pixel(1), 0)
            self.assertGreater(pixel(20), 100)
            self.assertEqual(pixel(36), 0)

    def test_empty_interval_adds_nothing(self):
        args, filters = [], []
        self.assertEqual(add_news_card(args, filters, 'base', ROOT, '.', 0,
                                      '', '', '', 1, 1, True, FONT), 'base')
        self.assertEqual(args, [])
        self.assertEqual(filters, [])

    def test_section_transition_only_on_changes_and_within_story(self):
        from scripts.motion_graphics import section_transition_end
        sections = ['regional', 'regional', 'sport']
        self.assertEqual(section_transition_end(sections, 0, 2, 6, True, 1.6), 3.6)
        self.assertEqual(section_transition_end(sections, 1, 6, 8, True, 1.6), 6)
        self.assertEqual(section_transition_end(sections, 2, 8, 8.2, True, 1.6), 8.2)
        self.assertEqual(section_transition_end(sections, 0, 2, 6, False, 1.6), 2)

    def test_section_transition_renders_and_disappears(self):
        from scripts.motion_graphics import add_section_transition
        with tempfile.TemporaryDirectory() as tmp:
            args = ['ffmpeg', '-v', 'error', '-y', '-filter_complex_threads', '1',
                    '-f', 'lavfi', '-i', 'color=black:s=1280x720:r=20:d=2']
            filters = []
            current = add_section_transition(args, filters, '0:v', ROOT, tmp, 0,
                                             'Österreich', .25, 1.5, FONT)
            args += ['-filter_complex', ';'.join(filters), '-map', f'[{current}]',
                     '-t', '2', '-threads', '1', str(Path(tmp) / 'frame-%02d.png')]
            subprocess.run(args, check=True, capture_output=True)
            def pixel(frame):
                with Image.open(Path(tmp) / f'frame-{frame:02d}.png') as image:
                    return sum(image.getpixel((57, 80))[:3])
            self.assertEqual(pixel(1), 0)
            self.assertGreater(pixel(20), 100)
            self.assertEqual(pixel(36), 0)
