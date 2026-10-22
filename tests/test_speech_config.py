"""Unit checks for the free speech-engine selection."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate


class SpeechConfigurationTests(unittest.TestCase):
    def test_invalid_engine_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = copy.deepcopy(generate.CONFIG)
            cfg["tts_engine"] = "external_paid"
            with patch.object(generate, "CONFIG", cfg):
                with self.assertRaises(ValueError):
                    generate.synthesize("Hallo", Path(temp) / "voice.wav")

    def test_espeak_does_not_call_piper(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = copy.deepcopy(generate.CONFIG)
            cfg["tts_engine"] = "espeak"
            cfg["voice_pitch_semitones"] = 0
            with patch.object(generate, "CONFIG", cfg), patch.object(generate, "run") as run, patch.object(generate, "adjust_voice_pitch"):
                generate.synthesize("Hallo", Path(temp) / "voice.wav")
                args = run.call_args.args[0]
                self.assertEqual(args[0], "espeak-ng")


if __name__ == "__main__":
    unittest.main()
