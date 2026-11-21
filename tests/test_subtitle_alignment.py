"""Subtitle cues follow the synthesized speech (T063)."""
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import subtitle_alignment as sa  # noqa: E402
from scripts.generate import write_subtitles  # noqa: E402

RATE = 16000
TEXT = ('Die Bundesregierung hat am Freitag ein neues Klimapaket beschlossen. '
        'Es sieht höhere Förderungen für Wärmepumpen, den Ausbau der Bahn und neue Radwege in allen Landeshauptstädten vor. '
        'Verletzt wurde niemand. '
        'Die Opposition kritisiert, dass die Finanzierung ab 2028 offen sei.')


def fake_speech(text, path, word=0.055, gap=0.07, comma=0.2, sentence_gap=0.4, lead=0.12, seed=1):
    """Noise bursts per word with known pauses; returns true sentence intervals and cue-chunk starts."""
    rng = random.Random(seed)
    frames, t, truth = bytearray(), lead, []
    silence = lambda seconds: bytearray(2 * round(seconds * RATE))  # noqa: E731

    def burst(seconds):
        out = bytearray()
        for _ in range(round(seconds * RATE)):
            out += int(rng.uniform(-8000, 8000)).to_bytes(2, 'little', signed=True)
        return out
    frames += silence(lead)
    sentences = sa.split_sentences(text)
    for s_index, sentence in enumerate(sentences):
        start = t
        words = sentence.split()
        for w_index, token in enumerate(words):
            length = word * max(2, len(token))
            frames += burst(length)
            t += length
            if w_index < len(words) - 1:
                pause = comma if token.endswith(',') else gap
                frames += silence(pause)
                t += pause
        truth.append((start, t))
        if s_index < len(sentences) - 1:
            frames += silence(sentence_gap)
            t += sentence_gap
    frames += silence(0.3)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(bytes(frames))
    return sentences, truth, t + 0.3


class SentenceSplitTests(unittest.TestCase):
    def test_abbreviations_ordinals_and_lower_case_words(self):
        self.assertEqual(sa.split_sentences('Bahn vor. Er kam am 3. November an. Das ist z. B. so, bzw. anders! Ende?'),
                         ['Bahn vor.', 'Er kam am 3. November an.', 'Das ist z. B. so, bzw. anders!', 'Ende?'])
        self.assertEqual(sa.split_sentences('  '), [])


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_sentence_boundaries_within_half_a_second(self):
        sentences, truth, _ = fake_speech(TEXT, self.dir / 'a.wav')
        times, _ = sa.sentence_times(sentences, self.dir / 'a.wav')
        errors = [abs(a - b) for t, m in zip(truth, times) for a, b in zip(t, m)]
        self.assertLess(max(errors), 0.05)

    def test_comma_pauses_are_not_taken_for_sentence_ends(self):
        # Long pauses at commas but even longer ones at sentence ends.
        sentences, truth, _ = fake_speech(TEXT, self.dir / 'b.wav', comma=0.3, sentence_gap=0.45)
        times, _ = sa.sentence_times(sentences, self.dir / 'b.wav')
        self.assertLess(max(abs(t[0] - m[0]) for t, m in zip(truth, times)), 0.05)

    def test_cues_never_span_sentences_and_start_with_speech(self):
        sentences, truth, _ = fake_speech(TEXT, self.dir / 'c.wav')
        cues = sa.aligned_cues(TEXT, self.dir / 'c.wav', offset=10.0)
        starts = [c[0] / 1000 - 10 for c in cues]
        for start, _end in truth:
            self.assertLess(min(abs(start - s) for s in starts), 0.05)
        joined = ' '.join(c[2].replace('\n', ' ') for c in cues)
        self.assertEqual(joined, ' '.join(sentences))
        self.assertEqual(cues, sorted(cues))
        self.assertTrue(all(b > a for a, b, _ in cues))

    def test_missing_pauses_fall_back_to_proportional_timing(self):
        with wave.open(str(self.dir / 'd.wav'), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(RATE)
            rng = random.Random(2)
            output.writeframes(b''.join(int(rng.uniform(-8000, 8000)).to_bytes(2, 'little', signed=True)
                                        for _ in range(RATE * 4)))
        times, _ = sa.sentence_times(['Eins zwei drei.', 'Vier fünf sechs.'], self.dir / 'd.wav')
        self.assertAlmostEqual(times[0][1], 2.0, delta=0.15)

    def test_silent_file_gives_no_cues(self):
        with wave.open(str(self.dir / 'e.wav'), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(RATE)
            output.writeframes(bytes(RATE * 2))
        self.assertEqual(sa.aligned_cues('Hallo Welt.', self.dir / 'e.wav'), [])

    def test_write_subtitles_uses_audio_and_writes_vtt_and_srt(self):
        sentences, truth, length = fake_speech(TEXT, self.dir / 'f.wav')
        write_subtitles(['Intro.', TEXT], [0.0, 2.0, 2.0 + length], self.dir, [1.5, length],
                        [self.dir / 'missing.wav', self.dir / 'f.wav'])
        vtt = (self.dir / 'subtitles.de.vtt').read_text()
        srt = (self.dir / 'subtitles.de.srt').read_text()
        self.assertTrue(vtt.startswith('WEBVTT'))
        self.assertIn('00:00:00.000 --> 00:00:01.500\nIntro.', vtt)  # unreadable audio: proportional fallback
        starts = [int(m[0]) * 3600 + int(m[1]) * 60 + float(m[2].replace(',', '.'))
                  for m in re.findall(r'(\d\d):(\d\d):(\d\d,\d{3}) -->', srt)]
        for start, _end in truth:
            self.assertLess(min(abs(2.0 + start - s) for s in starts), 0.05)


@unittest.skipUnless(shutil.which('espeak-ng'), 'eSpeak-NG needed')
class SpeechSampleTests(unittest.TestCase):
    """Sample with real synthesis: sentences spoken separately, joined with Piper's pause."""

    def test_espeak_sample_deviation_below_half_a_second(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sentences = sa.split_sentences(TEXT)
            truth, t, params, frames = [], 0.0, None, b''
            for index, sentence in enumerate(sentences):
                path = tmp / f'{index}.wav'
                subprocess.run(['espeak-ng', '-v', 'de', '-s', '145', '-w', str(path), sentence], check=True)
                start, end, _ = sa.speech_map(path)
                with wave.open(str(path)) as source:
                    params = source.getparams()
                    frames += source.readframes(source.getnframes())
                    duration = source.getnframes() / source.getframerate()
                truth.append((t + start, t + end))
                t += duration
                if index < len(sentences) - 1:
                    pause = round(0.38 * params.framerate) * params.sampwidth
                    frames += bytes(pause)
                    t += pause / params.sampwidth / params.framerate
            with wave.open(str(tmp / 'all.wav'), 'wb') as output:
                output.setparams(params)
                output.writeframes(frames)
            times, _ = sa.sentence_times(sentences, tmp / 'all.wav')
            errors = [abs(a - b) for x, y in zip(truth, times) for a, b in zip(x, y)]
            self.assertLess(max(errors), 0.5)


if __name__ == '__main__':
    unittest.main()
