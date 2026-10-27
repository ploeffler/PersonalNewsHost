"""Live render labels must follow output time and preserve renderer failures."""
import contextlib
import io
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate


class RenderProgressTests(unittest.TestCase):
    def setUp(self):
        self.titles = ['Erste Meldung', 'Zweite Meldung']
        self.boundaries = [0, 2, 5, 15, 25, 30]

    def test_scene_boundaries(self):
        for seconds, expected in ((0, 'Intro'), (4.99, 'Intro'),
                                  (5, 'Beitrag 1/2: Erste Meldung'),
                                  (14.99, 'Beitrag 1/2: Erste Meldung'),
                                  (15, 'Beitrag 2/2: Zweite Meldung'),
                                  (25, 'Outro'), (30, 'Outro')):
            with self.subTest(seconds=seconds):
                self.assertEqual(generate.render_stage(seconds, self.titles, self.boundaries), expected)

    def test_titles_stay_on_one_log_line(self):
        self.assertEqual(generate.render_stage(5, ['Überflutung\n in\tGraz'], [0, 2, 5, 15, 20]),
                         'Beitrag 1/1: Überflutung in Graz')

    def test_read_partial_and_missing_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'progress'
            self.assertIsNone(generate.render_time(path))
            path.write_text('out_time_us=N/A\n')
            self.assertIsNone(generate.render_time(path))
            path.write_text('out_time_us=5000000\nprogress=continue\nout_time_us=15250000\nprogress=continue\n')
            self.assertEqual(generate.render_time(path), 15.25)
            path.write_text('out_time_us=5000000\nout_time_us=N/A\n')
            self.assertEqual(generate.render_time(path), 5)

    def test_ffmpeg_progress_is_enabled_and_completion_logged(self):
        output = io.StringIO()
        def execute(args):
            progress = Path(args[args.index('-progress') + 1])
            progress.write_text('out_time_us=30000000\nprogress=end\n')
            self.assertEqual(args[-1], 'output.mp4')
        with patch.object(generate, 'run', side_effect=execute) as run, contextlib.redirect_stdout(output):
            generate.run_render(['ffmpeg', '-y', 'output.mp4'], self.titles, self.boundaries)
        run.assert_called_once()
        self.assertIn('[Render] Intro', output.getvalue())
        self.assertIn('[Render] Outro | Videozeit 30.0/30.0 s', output.getvalue())
        self.assertIn('Rendering abgeschlossen.', output.getvalue())

    def test_timeout_and_process_errors_are_propagated(self):
        for error in (subprocess.TimeoutExpired('ffmpeg', 480), subprocess.CalledProcessError(1, 'ffmpeg')):
            with self.subTest(error=error), patch.object(generate, 'run', side_effect=error), contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(type(error)):
                    generate.run_render(['ffmpeg', 'output.mp4'], self.titles, self.boundaries)
                self.assertNotIn('Rendering abgeschlossen.', output.getvalue())

    def test_contribution_is_reported_before_render_process_finishes(self):
        reported = threading.Event()
        messages = []
        def emit(message, **kwargs):
            self.assertTrue(kwargs.get('flush'))
            messages.append(message)
            if 'Beitrag 2/2: Zweite Meldung' in message:
                reported.set()
        def execute(args):
            progress = Path(args[args.index('-progress') + 1])
            progress.write_text('out_time_us=15000000\nprogress=continue\n')
            self.assertTrue(reported.wait(3), 'Current contribution was not reported while FFmpeg was running')
            self.assertNotIn('[Render] Rendering abgeschlossen.', messages)
        with patch.object(generate, 'print', side_effect=emit, create=True), patch.object(generate, 'run', side_effect=execute):
            generate.run_render(['ffmpeg', 'output.mp4'], self.titles, self.boundaries)
        self.assertEqual(messages[-1], '[Render] Rendering abgeschlossen.')
