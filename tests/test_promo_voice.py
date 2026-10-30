from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch
from scripts.promo_voice import synthesize,PRODUCTION_VOICE,spoken_outro,BRAND_IPA

class VoiceTests(unittest.TestCase):
    def test_english_brand_override_only_in_spoken_outro(self):
        for brand in ['FullFeaturedOutlet','FullfeaturedOutlet']:
            script='Deutsche Nachrichten.\n\nErstellt mit '+brand+'.'
            self.assertEqual(spoken_outro(script),'Deutsche Nachrichten.\n\nErstellt mit [['+BRAND_IPA+']].')
        article='FullFeaturedOutlet ist ein Produkt. Ein Bericht darüber.'
        self.assertEqual(spoken_outro(article),article)
    def write_wav(self,path):
        with wave.open(str(path),'wb') as wav:
            wav.setparams((1,2,22050,0,'NONE','not compressed'));wav.writeframes(b'\x10\x08'*22050)
    def test_main_production_values(self):
        self.assertEqual(PRODUCTION_VOICE['voice_model'],'de_DE-thorsten-high')
        self.assertEqual(PRODUCTION_VOICE['piper_length_scale'],1.06)
        self.assertEqual(PRODUCTION_VOICE['sentence_silence'],.38)
        self.assertEqual(PRODUCTION_VOICE['voice_pitch_semitones'],-1.5)
    def test_missing_piper_is_visible_not_silent_espeak(self):
        with tempfile.TemporaryDirectory() as d,patch('scripts.promo_voice.shutil.which',return_value=None):
            with self.assertRaises(RuntimeError):synthesize('Hallo',Path(d)/'v.wav',Path(d),fallback=lambda *a:self.fail('silent fallback'))
    def test_piper_arguments_and_pitch_preserve_duration(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'models').mkdir();(root/'models/de_DE-thorsten-high.onnx').touch();(root/'models/de_DE-thorsten-high.onnx.json').touch();path=root/'v.wav'
            def run(args,**kwargs):
                if args[0]=='piper':self.write_wav(path)
                else:self.write_wav(Path(args[-1]))
            with patch('scripts.promo_voice.shutil.which',return_value='piper'),patch('scripts.promo_voice.subprocess.run',side_effect=run) as invoke:
                report=synthesize('Erstellt mit FullFeaturedOutlet.',path,root)
            args=invoke.call_args_list[0].args[0]
            self.assertIn('1.06',args);self.assertIn('0.38',args)
            self.assertIn('atempo=',invoke.call_args_list[1].args[0][-6])
            self.assertEqual(report['actual_engine'],'piper')
            self.assertEqual(invoke.call_args_list[0].kwargs['input'],'Erstellt mit [['+BRAND_IPA+']].')
            self.assertEqual(report['outro_pronunciation']['language'],'en-GB')
    def test_invalid_values_never_start_engine(self):
        with patch('scripts.promo_voice.subprocess.run') as run:
            with self.assertRaises(ValueError):synthesize('x',Path('x.wav'),Path('.'),profile={'voice_pitch_semitones':float('nan')})
            run.assert_not_called()
