"""Hosts and studio variants per show (T060)."""
import copy
import json
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from scripts import generate
from scripts.produce_show import produce
from scripts.shows import resolve_shows
from scripts.validate_config import validate_config

ROOT = Path(__file__).resolve().parents[1]


def example():
    return json.loads((ROOT / 'config.shows.example.json').read_text(encoding='utf-8'))


class ResolutionTests(unittest.TestCase):
    def test_example_shows_use_different_hosts_and_studios(self):
        validate_config(example())
        main, tech = (show['config'] for show in resolve_shows(example()))
        self.assertEqual((main['host_id'], main['studio_id']), ('newshost', 'classic'))
        self.assertEqual((tech['host_id'], tech['studio_id'], tech['co_host_id']), ('tech', 'tech', 'newshost'))
        self.assertNotEqual(main['presenter_settings']['portrait'], tech['presenter_settings']['portrait'])
        self.assertNotEqual(main['presenter_settings']['scenes']['intro_static_color'],
                            tech['presenter_settings']['scenes']['intro_static_color'])
        self.assertNotEqual(main['voice_pitch_semitones'], tech['voice_pitch_semitones'])
        self.assertEqual(tech['presenter_settings']['name'], 'TechHost')
        self.assertEqual([p['name'] for p in tech['voice_profiles']], ['TechHost', 'NewsHost'])
        self.assertEqual(tech['voice_profiles'][1]['voice_pitch_semitones'], -1.5)
        self.assertNotIn('hosts', tech)
        self.assertNotIn('studios', tech)
        # Studio scenes merge with inherited scene settings.
        self.assertIn('outro_text', tech['presenter_settings']['scenes'])

    def test_explicit_show_fields_win_over_registry(self):
        config = example()
        config['shows'][1]['presenter'] = 'assets/own.png'
        config['shows'][1]['voice_pitch_semitones'] = 0
        tech = resolve_shows(config)[1]['config']
        self.assertEqual(tech['presenter_settings']['portrait'], 'assets/own.png')
        self.assertEqual(tech['voice_pitch_semitones'], 0)

    def test_invalid_references_are_rejected(self):
        for change, message in [
                ({'host_id': 'missing'}, 'Unknown host_id'),
                ({'studio_id': 'missing'}, 'Unknown studio_id'),
                ({'host_id': 'tech', 'co_host_id': 'tech'}, 'must differ'),
                ({'co_host_id': 'tech', 'host_id': None}, 'Unknown host_id')]:
            config = example()
            config['shows'][0].update(change)
            if change.get('host_id') is None and 'host_id' in change:
                config['shows'][0].pop('host_id')
                message = 'requires host_id'
            with self.assertRaisesRegex(ValueError, message):
                resolve_shows(config)
        config = example()
        config['hosts']['tech']['password'] = 'x'
        with self.assertRaisesRegex(ValueError, 'Unknown hosts field'):
            resolve_shows(config)
        config = example()
        config['studios']['Bad ID'] = {}
        with self.assertRaises(ValueError):
            resolve_shows(config)

    def test_legacy_config_is_untouched(self):
        config = example()
        config.pop('shows')
        self.assertEqual(resolve_shows(config)[0]['config'], config)


class VoiceTests(unittest.TestCase):
    def test_stories_alternate_between_hosts(self):
        profiles = [{'name': 'A'}, {'name': 'B'}]
        with patch.object(generate, 'CONFIG', {'voice_profiles': profiles}):
            voices = [generate.segment_voice(i, 7) for i in range(7)]
        self.assertEqual([v and v['name'] for v in voices], [None, None, 'A', 'B', 'A', 'B', None])
        with patch.object(generate, 'CONFIG', {'voice_profiles': profiles[:1]}):
            self.assertIsNone(generate.segment_voice(3, 7))

    def test_piper_voice_falls_back_to_installed_default(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(generate, 'ROOT', Path(tmp)):
            (Path(tmp) / 'models').mkdir()
            (Path(tmp) / 'models/de_DE-kerstin-low.onnx').write_bytes(b'x')
            with patch.object(generate, 'CONFIG', {'presenter_settings': {'voice_model': 'de_DE-kerstin-low'}}):
                self.assertEqual(generate.piper_model()[0], 'de_DE-kerstin-low')
                self.assertEqual(generate.piper_model({'voice_model': 'de_DE-eva_k-x_low'})[0], 'de_DE-thorsten-high')
                self.assertEqual(generate.piper_model({'voice_model': '../../etc/passwd'})[0], 'de_DE-thorsten-high')

    def test_espeak_uses_profile_voice_and_pitch(self):
        calls, pitches = [], []
        config = {'tts_engine': 'espeak', 'voice': 'de', 'voice_pitch_semitones': -1.5}
        with patch.object(generate, 'CONFIG', config), patch.object(generate, 'run', side_effect=calls.append), \
                patch.object(generate, 'adjust_voice_pitch', side_effect=lambda wav, profile=None: pitches.append(profile)):
            generate.synthesize('Hallo', Path('x.wav'), {'voice': 'de+f3', 'voice_pitch_semitones': 2})
            generate.synthesize('Hallo', Path('y.wav'))
        self.assertEqual(calls[0][:3], ['espeak-ng', '-v', 'de+f3'])
        self.assertEqual(calls[1][:3], ['espeak-ng', '-v', 'de'])
        self.assertEqual(pitches, [{'voice': 'de+f3', 'voice_pitch_semitones': 2}, {}])


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class ProductionTests(unittest.TestCase):
    def test_two_shows_produce_with_their_own_host_and_studio(self):
        config = example()
        config.update(feeds=['https://example.org/rss'], max_items=2)
        config['editorial'] = {'pipeline': {'enabled': False}, 'crosscheck': {'enabled': False}}
        config['media'] = {'mode': 'off', 'web_image_fallback': False, 'enhancement': 'off'}
        config['article_enrichment'] = {'enabled': False}
        config['presenter_settings']['scenes'].update(intro_mode='static', show_headlines=False)
        config['presenter_settings']['lip_sync'] = {'enabled': False}
        for host in config['hosts'].values():
            host['lip_sync'] = {'enabled': False}
        spoken = []

        def audio(text, destination, profile=None):
            spoken.append((generate.CONFIG.get('host_id'), (profile or {}).get('name'), text[:20]))
            with wave.open(str(destination), 'wb') as wav:
                wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(32000))
        items = [('Erste Meldung zum Test', 'Text eins.', 'https://example.org/a', []),
                 ('Zweite Wetterwarnung heute', 'Text zwei.', 'https://example.org/b', [])]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            with patch.object(generate, 'items_from_feed', return_value=items), \
                    patch.object(generate, 'extract_article_text', return_value=''), \
                    patch.object(generate, 'synthesize', side_effect=audio):
                for ident in ('main', 'technology'):
                    produce(config, ident, out)
            meta = {i: json.loads((out / i / 'show.json').read_text()) for i in ('main', 'technology')}
            self.assertEqual((meta['main']['host_id'], meta['main']['studio_id']), ('newshost', 'classic'))
            self.assertEqual((meta['technology']['host_id'], meta['technology']['studio_id']), ('tech', 'tech'))
            for ident in ('main', 'technology'):
                self.assertGreater((out / ident / 'latest.mp4').stat().st_size, 1000)
        # Speech runs in parallel, so compare by story text rather than call order.
        story_voices = {text: voice for host, voice, text in spoken if host == 'tech' and voice}
        self.assertEqual(story_voices, {'Erste Meldung zum Te': 'TechHost', 'Zweite Wetterwarnung': 'NewsHost'})
        self.assertFalse([voice for host, voice, _ in spoken if host == 'newshost' and voice])


if __name__ == '__main__':
    unittest.main()
