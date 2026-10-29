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
    def render(self, mode, kind="color", station_logo=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "assets").mkdir()
            image = root / "assets" / "intro.ppm"
            image.write_bytes(b"P6\n2 2\n255\n" + bytes([255, 0, 0] * 4))
            cfg = copy.deepcopy(generate.CONFIG)
            cfg.update({"title": "Test", "feeds": ["https://example.org/rss"],
                        "max_items": 1, "max_description_chars": 30,
                        "tts_engine": "espeak", "voice_pitch_semitones": 0,
                        "station_logo": ""})
            if station_logo:
                from PIL import Image
                logo = Image.new("RGBA", (160, 90), (0, 0, 0, 0))
                logo.paste((255, 0, 0, 255), (80, 0, 160, 90))
                if station_logo == "default":
                    logo.save(root / "assets/logo-video.png")
                    cfg.pop("station_logo")
                else:
                    logo.save(root / "assets/station-logo.png")
                    cfg["station_logo"] = "assets/station-logo.png"
            cfg["presenter_settings"] = {
                "name": "Test", "portrait": "assets/missing.png",
                "background": "assets/missing.jpg",
                "scenes": {"intro_mode": mode, "intro_static_type": kind,
                           "intro_static_color": "#13243a",
                           "intro_static_image": "assets/intro.ppm",
                           "intro_seconds": 1, "outro_seconds": 1,
                           "show_headlines": True}}
            def audio(_text, destination):
                with wave.open(str(destination), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(bytes(16000 * 5 * 2))
            with patch.object(generate, "ROOT", root), patch.object(generate, "DOCS", root / "docs"), patch.object(generate, "CONFIG", cfg), patch.object(generate, "items_from_feed", return_value=[("Testmeldung", "Kurzer Text", "https://example.org")]), patch.object(generate, "synthesize", side_effect=audio):
                generate.main()
            page = (root / "docs" / "index.html").read_text()
            self.assertIn("<track kind='subtitles'", page)
            self.assertIn("subtitles.de.vtt?v=", page)
            video = root / "docs" / "latest.mp4"
            self.assertGreater(video.stat().st_size, 1000)
            for name in ("index.html", "feed.xml", "transcript.txt", "subtitles.de.vtt", "subtitles.de.srt"):
                self.assertTrue((root / "docs" / name).is_file())
            if station_logo:
                duration = float(subprocess.check_output([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", str(video)], text=True))
                # Verify the mark stays above the static intro, story and outro.
                for moment in (0.2, duration / 2, duration - 0.2):
                    pixels = subprocess.check_output([
                        "ffmpeg", "-v", "error", "-ss", str(moment), "-i", str(video),
                        "-vf", "format=rgb24,crop=160:90:1090:30", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"])
                    red = pixels[(20 * 160 + 110) * 3: (20 * 160 + 110) * 3 + 3]
                    self.assertGreater(red[0], 180)
                    self.assertLess(red[1], 80)
                    # The transparent half reveals the scene, rather than black fill.
                    clear = pixels[(20 * 160 + 20) * 3: (20 * 160 + 20) * 3 + 3]
                    self.assertGreater(sum(clear), 30)

    def test_avatar_intro(self):
        self.render("avatar")

    def test_static_color_intro(self):
        self.render("static", "color")

    def test_static_image_intro(self):
        self.render("static", "image")

    def test_transparent_station_logo_throughout_broadcast(self):
        self.render("static", "color", station_logo=True)

    def test_default_station_logo_without_config_field(self):
        self.render("static", "color", station_logo="default")


if __name__ == "__main__":
    unittest.main()
