import tempfile
import unittest
from pathlib import Path
from scripts.generate import write_subtitles, subtitle_timestamp


class SubtitleTests(unittest.TestCase):
    def test_timestamps_carry_and_long_duration(self):
        self.assertEqual(subtitle_timestamp(3600001), "01:00:00.001")
        self.assertEqual(subtitle_timestamp(60000, ","), "00:01:00,000")

    def test_speech_boundaries_and_literal_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_subtitles(["Hallo <Welt> & Österreich.", "Wort " * 40], [0, 1.25, 12], root)
            vtt = (root / "subtitles.de.vtt").read_text()
            srt = (root / "subtitles.de.srt").read_text()
            self.assertTrue(vtt.startswith("WEBVTT\n\n"))
            self.assertIn("00:00:00.000 --> 00:00:01.250", vtt)
            self.assertIn("Hallo &lt;Welt&gt; &amp; Österreich.", vtt)
            self.assertIn("00:00:01.250 -->", vtt)
            self.assertIn("00:00:12.000", vtt)
            self.assertIn("1\n00:00:00,000 --> 00:00:01,250", srt)
            ranges = [line.split(" --> ") for line in vtt.splitlines() if " --> " in line]
            self.assertTrue(all(a < b for a, b in ranges))
            self.assertTrue(all(ranges[i][1] == ranges[i+1][0] for i in range(len(ranges)-1)))

    def test_empty_and_zero_length_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_subtitles(["", "Still"], [0, 1, 1], root)
            self.assertEqual((root / "subtitles.de.vtt").read_text(), "WEBVTT\n\n")
            self.assertEqual((root / "subtitles.de.srt").read_text(), "")

    def test_reject_mismatched_segments(self):
        with self.assertRaises(ValueError):
            write_subtitles(["Hallo"], [0], Path("unused"))
