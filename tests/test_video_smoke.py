"""Offline FFmpeg smoke tests for configured intro modes; no RSS or paid services."""
import copy
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from scripts import generate


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class VideoSmokeTests(unittest.TestCase):
    def render(self, mode, kind="color"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "assets").mkdir()
            image = root / "assets" / "intro.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                            "-i", "color=c=red:s=320x240:d=1", "-frames:v", "1",
                            str(image)], check=True)
            cfg = copy.deepcopy(generate.CONFIG)
            cfg.update({"title": "Test", "feeds": ["https://example.org/rss"],
                        "max_items": 1, "max_description_chars": 30,
                        "tts_engine": "espeak", "voice_pitch_semitones": 0})
            cfg["presenter_settings"] = {
                "name": "Test", "portrait": "assets/missing.png",
                "background": "assets/missing.jpg",
                "scenes": {"intro_mode": mode, "intro_static_type": kind,
                           "intro_static_color": "#13243a",
                           "intro_static_image": "assets/intro.png",
                           "intro_seconds": 1, "outro_seconds": 1,
                           "show_headlines": True}}
            def audio(_text, destination):
                with wave.open(str(destination), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(b"\\0\\0" * 16000 * 5)
            with patch.object(generate, "ROOT", root), patch.object(generate, "DOCS", root / "docs"), patch.object(generate, "CONFIG", cfg), patch.object(generate, "items_from_feed", return_value=[("Testmeldung", "Kurzer Text", "https://example.org")]), patch.object(generate, "synthesize", side_effect=audio):
                generate.main()
            video = root / "docs" / "latest.mp4"
            self.assertGreater(video.stat().st_size, 1000)
            for name in ("index.html", "feed.xml", "transcript.txt"):
                self.assertTrue((root / "docs" / name).is_file())

    def test_avatar_intro(self):
        self.render("avatar")

    def test_static_color_intro(self):
        self.render("static", "color")

    def test_static_image_intro(self):
        self.render("static", "image")


if __name__ == "__main__":
    unittest.main()
