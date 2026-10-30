"""Offline preview, operator evidence, animation and real local-video contracts."""
import copy
import ctypes.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave
from unittest.mock import patch

from scripts import promo_video as promo
from scripts import promo_network as network

FEED = b'''<rss><channel><title>Beispiel Technik</title><link>https://publisher.example/</link>
<item><title>Neue Bahnstrecke wird eroeffnet</title><link>https://publisher.example/a</link><description>Die Bahnstrecke wird heute eroeffnet. Sie verbindet zwei Staedte. Ein dritter Satz.</description></item>
<item><title>Ist die Bruecke wieder frei?</title><link>https://publisher.example/b</link></item>
</channel></rss>'''


def fixture():
    return promo.preview('https://publisher.example/rss',data=FEED,research=False,count=2)


class PromoTests(unittest.TestCase):
    def test_short_summaries_intro_outro_and_host_background_suggestions(self):
        p=fixture();promo.validate_plan(p)
        self.assertEqual(p['intro'],'Ich bin NewsHost, herzlich willkommen!')
        self.assertEqual(p['outro'],'Erstellt mit FullFeaturedOutlet.')
        self.assertEqual(len(promo.sentence_units(p['stories'][0]['summary'])),2)
        self.assertNotIn('dritter',p['stories'][0]['summary'])
        self.assertTrue(p['stories'][1]['summary'].endswith('?'))
        self.assertEqual(len(p['background_suggestions']),3)
        self.assertTrue(p['host_suggestions'])
        self.assertEqual(p['operator']['status'],'unverified')

    def test_all_render_options_are_offered_with_honest_readiness(self):
        p=fixture();options={x['id']:x for x in p['render_options']}
        self.assertEqual(set(options),{'2d-local','3d-local','3d-online'})
        self.assertEqual(options['2d-local']['status'],'ready')
        self.assertEqual(options['3d-local']['status'],'setup_required')
        self.assertEqual(options['3d-online']['status'],'setup_required')
        self.assertIsNone(options['3d-online']['cost_preview'])
        self.assertTrue(options['3d-online']['requires_approval'])
        self.assertTrue(options['3d-online']['data_to_transfer'])

    def test_unconfigured_3d_never_uploads_or_silently_renders_2d(self):
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'out'
            for mode in ['3d-local','3d-online']:
                p=fixture();p['render_mode']=mode
                with patch.object(promo,'speak',side_effect=AssertionError('must not start')), patch.object(promo,'fetch_public',side_effect=AssertionError('must not upload')):
                    with self.assertRaises(promo.RenderNotConfigured):promo.render(p,output)
                self.assertFalse(output.exists())

    def test_maximum_card_text_fits_visible_pixel_box(self):
        from PIL import Image, ImageDraw
        text='LangerMeldungstitel '*13+'\n\n'+'Ein langer Nachrichtentext '*13+'.'
        font,wrapped=promo.fit_card(text)
        box=ImageDraw.Draw(Image.new('RGB',(960,540))).multiline_textbbox((30,100),wrapped,font=font,spacing=6)
        self.assertLessEqual(box[2],480);self.assertLessEqual(box[3],490)
        # Preserve all non-whitespace characters, including unbroken long names.
        self.assertEqual(''.join(wrapped.split()),''.join(text.split()))
        font,wrapped=promo.fit_card('A'*250+'\n\n'+'B'*350+'.')
        box=ImageDraw.Draw(Image.new('RGB',(1,1))).multiline_textbbox((0,0),wrapped,font=font,spacing=6)
        self.assertLessEqual(box[2],450);self.assertLessEqual(box[3],390)

    def test_operator_research_follows_legal_page_and_records_self_declaration(self):
        pages={'https://publisher.example/':b'<a href="/impressum">Impressum</a>',
               'https://publisher.example/impressum':b'<p>Medieninhaber: Beispiel Medien GmbH.</p>'}
        p=promo.preview('https://publisher.example/rss',data=FEED,fetch=lambda u:pages[u])
        self.assertEqual(p['operator']['status'],'self_declared')
        self.assertEqual(p['operator']['operator'],'Beispiel Medien GmbH')
        self.assertEqual(p['operator']['evidence'][-1]['url'],'https://publisher.example/impressum')

    def test_unavailable_operator_is_not_invented(self):
        def unavailable(url):raise OSError('offline')
        p=promo.preview('https://publisher.example/rss',data=FEED,fetch=unavailable)
        self.assertEqual(p['operator']['status'],'unverified');self.assertIsNone(p['operator']['operator'])

    def test_research_is_bounded(self):
        calls=[]
        def page(url):
            calls.append(url)
            return b'<a href="/impressum">x</a><a href="/legal">x</a><a href="/about">x</a>'
        promo.preview('https://publisher.example/rss',data=FEED,fetch=page)
        self.assertLessEqual(len(calls),3)

    def test_entities_oversize_and_private_urls_are_rejected(self):
        for data in [b'<!DOCTYPE rss [<!ENTITY x "bad">]><rss/>',b'x'*(network.MAX_FEED_BYTES+1)]:
            with self.assertRaises(ValueError):promo.preview('https://publisher.example/rss',data=data,research=False)
        for url in ['http://127.0.0.1/rss','http://localhost/rss','http://[::1]/rss','https://example.org/rss?token=private','https://u:p@example.org/rss']:
            with self.assertRaises(ValueError):network.validate_feed_url(url,resolve=False)
        with patch.object(network.socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',80))]):
            with self.assertRaises(ValueError):network.checked_connection(('publisher.example',80))

    def test_plan_validation_rejects_changed_texts_or_too_many_sentences(self):
        for key in ['intro','outro']:
            p=fixture();p[key]='different'
            with self.assertRaises(ValueError):promo.validate_plan(p)
        p=fixture();p['stories'][0]['summary']='Erster Satz. Zweiter Satz. Dritter Satz.'
        with self.assertRaises(ValueError):promo.validate_plan(p)

    def test_atom_summary_and_homepage(self):
        data=b'<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom</title><link href="https://publisher.example/"/><entry><title>Testmeldung</title><link href="https://publisher.example/a"/><summary>Eine kurze Nachricht.</summary></entry></feed>'
        p=promo.preview('https://publisher.example/atom',data=data,research=False)
        self.assertEqual(p['stories'][0]['summary'],'Eine kurze Nachricht.')

    @unittest.skipUnless(ctypes.util.find_library('espeak-ng'),'Local eSpeak-NG library required')
    def test_real_local_speech_has_nonzero_pcm(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'voice.wav';promo.speak('Ich bin NewsHost, herzlich willkommen!',path)
            with wave.open(str(path)) as w:
                self.assertGreater(w.getnframes(),w.getframerate());self.assertTrue(any(w.readframes(w.getnframes())))

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_complete_video_has_audio_archive_sources_and_motion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);audio=root/'voice.wav'
            # Explicit test audio, not a claimed speech/model production.
            with wave.open(str(audio),'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(b'\x10\x08'*16000)
            plan=fixture();manifest=promo.render(plan,root/'out',audio=audio,fps=5)
            video=Path(manifest['video']);self.assertTrue(video.is_file())
            self.assertRegex(video.as_posix(),r'/archive/\d{4}/\d{2}/\d{2}/[^/]+/werbevideo.mp4$')
            self.assertEqual(len(list((root/'out').rglob('*.mp4'))),1)
            self.assertEqual(manifest['sha256'],hashlib.sha256(video.read_bytes()).hexdigest())
            self.assertFalse(manifest['published']);self.assertEqual(len(json.loads((video.parent/'sources.json').read_text())),2)
            # Crop only the host region, excluding changing text and AI label.
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf','crop=420:380:510:90','-pix_fmt','rgb24','-f','rawvideo','-'])
            size=420*380*3;self.assertGreaterEqual(len(raw)//size,5)
            self.assertNotEqual(raw[:size],raw[3*size:4*size])
            # The bottom-right AI plate persists across the complete video.
            labels=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf','crop=57:38:893:492','-pix_fmt','rgb24','-f','rawvideo','-'])
            self.assertGreater(sum(labels[:57*38*3]),1000)
            self.assertGreater(sum(labels[-57*38*3:]),1000)

    def test_no_static_fallback_when_animation_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);audio=root/'voice.wav'
            with wave.open(str(audio),'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*16000)
            with patch.object(promo,'generate_frames',side_effect=ValueError('bad host')):
                with self.assertRaises(ValueError):promo.render(fixture(),root/'out',audio=audio)
            self.assertFalse(list((root/'out').rglob('*.mp4')))

    def test_production_voice_and_calibration_reach_render_adapters(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mouth={'x':.5,'y':.3,'width':.1,'height':.08}
            def speech(text,path,*args,**kwargs):
                with wave.open(str(path),'wb') as wav:
                    wav.setparams((1,2,16000,0,'NONE','not compressed'));wav.writeframes(b'\x10\x08'*16000)
                return {'actual_engine':'piper'}
            with patch.object(promo,'synthesize',side_effect=speech) as voice, patch.object(promo,'generate_frames',side_effect=ValueError('stop after adapters')) as frames:
                with self.assertRaises(ValueError):promo.render(fixture(),root/'out',mouth=mouth)
                self.assertEqual(voice.call_args.kwargs['profile']['tts_engine'],'piper')
                self.assertEqual(frames.call_args.kwargs['mouth'],mouth)
                self.assertEqual(frames.call_args.kwargs['fps'],20)


if __name__=='__main__':unittest.main()
