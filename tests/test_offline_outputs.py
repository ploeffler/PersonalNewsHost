"""Fixture RSS -> one grouped bulletin -> real media, feed and linked HTML."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import wave
import xml.etree.ElementTree as ET
from unittest.mock import patch
from scripts import check_repository, generate

ROOT = Path(__file__).resolve().parents[1]


class OfflineOutputTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_fixture_feed_produces_linked_page_and_valid_media_feed(self):
        fixture = (ROOT/'tests/fixtures/offline-feeds/news.xml').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root/'docs'
            docs.mkdir()
            # Existing navigation routes/assets are deployment inputs, not generated
            # by the bulletin. Keep them local and explicit in this fixture site.
            for name in ['short-updates.html','settings.html','browser-studio.html','editorial-pipeline.html']:
                (docs/name).write_text('<!doctype html><title>Local fixture route</title>')
            for name in ['playlist.js','playlist.css','news-list.js','news-list.css']:
                shutil.copyfile(ROOT/'docs'/name,docs/name)
            cfg = copy.deepcopy(generate.CONFIG)
            cfg.pop('shows',None)
            cfg.update(feeds=['https://fixture.example/rss'],max_items=2,station_logo='',parallel_workers=1)
            cfg['editorial']={'pipeline':{'enabled':False},'crosscheck':{'enabled':False}}
            cfg['media']={'mode':'off'}
            cfg['presenter_settings']={'portrait':'assets/missing.png','background':'assets/missing.jpg',
                'scenes':{'intro_mode':'static','intro_static_type':'color','show_headlines':False,'intro_seconds':1,'outro_seconds':1}}
            def audio(_text,path):
                with wave.open(str(path),'wb') as output:
                    output.setparams((1,2,16000,0,'NONE','not compressed'))
                    output.writeframes(b'\0\0'*3200)
            def feed_only(url):
                self.assertEqual(url,'https://fixture.example/rss')
                return fixture
            with check_repository.offline_network(), patch.object(generate,'ROOT',root), patch.object(generate,'DOCS',docs), patch.object(generate,'BASE','./'), patch.object(generate,'CONFIG',cfg), patch.object(generate,'fetch',side_effect=feed_only), patch.object(generate,'extract_article_text',return_value=''), patch.object(generate,'synthesize',side_effect=audio), patch.dict(generate.FEED_DATES,{},clear=True):
                generate.main()
            groups=json.loads((docs/'story-groups.json').read_text())
            self.assertEqual(len(groups),1)
            self.assertEqual({s['url'] for s in groups[0]['sources']},{'https://first.example/flood','https://second.example/flood'})
            feed=ET.parse(docs/'feed.xml')
            enclosure=feed.find('./channel/item/enclosure')
            self.assertEqual(enclosure.get('url'),'./latest.mp4')
            self.assertEqual(int(enclosure.get('length')),(docs/'latest.mp4').stat().st_size)
            self.assertEqual(enclosure.get('type'),'video/mp4')
            self.assertEqual(check_repository.site_links(docs),[])
            # A missing generated asset must fail the same checker used by CI.
            (docs/'subtitles.de.vtt').unlink()
            self.assertTrue(any('subtitles.de.vtt' in error for error in check_repository.site_links(docs)))
