"""Offline request/feed and actual FFmpeg composition contracts for chat reels."""
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from scripts import reel_show as reel


def request():
    return {'station_name':'Teststation','show_name':'Testshow','host_description':'fictional adult presenter',
            'studio_description':'blue studio','rss_feed':'https://news.example/rss','news_count':1,'output_name':'chat-reel','test_mode':False}


class ReelTests(unittest.TestCase):
    def test_workflow_request_reports_missing_fields_before_network(self):
        with patch.object(reel, 'read_feed', side_effect=AssertionError('network')):
            for config in [{}, {'station_name': 'Station'}]:
                with self.subTest(config=config), self.assertRaisesRegex(ValueError, 'missing: .*news_count'):
                    reel.normalize_request(config)
            for config in [None, [], 'text', 1]:
                with self.subTest(config=config), self.assertRaisesRegex(ValueError, 'JSON object'):
                    reel.normalize_request(config)

    def test_workflow_request_preserves_booleans_and_validates_numeric_counts(self):
        config = request();config['news_count'] = 1.0
        normalized = reel.normalize_request(config)
        self.assertIs(type(normalized['news_count']), int)
        self.assertIs(normalized['test_mode'], False)
        self.assertIs(type(config['news_count']), float)
        for count in [True, False, 1.5, '1', 0, 6]:
            config = request();config['news_count'] = count
            with self.subTest(count=count), self.assertRaises(ValueError):
                reel.normalize_request(config)
        for value in ['false', 'true', 1, None]:
            config = request();config['test_mode'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'JSON boolean'):
                reel.normalize_request(config)

    def test_input_validation_rejects_paths_controls_and_counts(self):
        reel.validate_inputs(request())
        for key, value in [('output_name','../escape'),('output_name','name;echo-bad'),('news_count',0),('news_count',6),('news_count',True),('station_name','x\ny')]:
            with self.subTest(key=key,value=value):
                config=request();config[key]=value
                with self.assertRaises(ValueError):reel.validate_inputs(config)

    def test_feed_rejects_credentials_private_addresses_and_entities(self):
        for url in ['file:///tmp/file','https://user:password@example.org/rss','https://example.org/rss?token=private']:
            with self.assertRaises(ValueError):reel.validate_feed_url(url,resolve=False)
        with patch.object(socket,'getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',80))]):
            with self.assertRaises(ValueError):reel.validate_feed_url('http://example.org/rss')
        with self.assertRaises(ValueError):reel.parse_feed(b'<!DOCTYPE rss><rss/>',1)
        with self.assertRaises(ValueError):reel.parse_feed(b'x'*(reel.MAX_FEED_BYTES+1),1)

    def test_test_mode_requires_actual_json_boolean(self):
        for value in ['false', 'true', 1, None]:
            config=request();config['test_mode']=value
            with self.assertRaises(ValueError):reel.validate_inputs(config)

    def test_connection_rechecks_and_binds_numeric_public_address(self):
        public=(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))
        private=(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))
        with patch.object(socket,'getaddrinfo',side_effect=[[public],[private]]), patch.object(socket,'socket') as factory:
            reel.validate_feed_url('https://news.example/rss')
            with self.assertRaises(ValueError):reel.checked_connection(('news.example',443),20)
            factory.assert_not_called()
        with patch.object(socket,'getaddrinfo',return_value=[public]), patch.object(socket,'socket') as factory:
            reel.checked_connection(('news.example',443),20)
            factory.return_value.connect.assert_called_once_with(('8.8.8.8',443))

    def test_chat_bridge_preserves_false_and_sends_safe_input_allowlist(self):
        from scripts import chat_reel
        import sys
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'request.json';config=request();config['ignored']='not sent';path.write_text(json.dumps(config))
            with patch.object(sys,'argv',['chat_reel',str(path)]), patch.object(chat_reel,'gh') as gh:
                chat_reel.main()
            body=gh.call_args.kwargs['body']
            forwarded=json.loads(body['inputs']['request'])
            self.assertIs(forwarded['test_mode'],False)
            self.assertNotIn('ignored',forwarded)
            self.assertEqual(body['inputs']['mode'],'reel')
            self.assertEqual(body['ref'],'Full-featured-Newsoutlet')

    def test_rss_atom_extractive_items_and_exact_requested_count(self):
        data=b'<rss><channel><item><title>One</title><description>Source text</description><link>https://source.example/a?tracking=x</link></item><item><title>One</title><link>https://source.example/b</link></item></channel></rss>'
        items=reel.parse_feed(data,1)
        self.assertEqual(items,[{'title':'One','text':'Source text','url':'https://source.example/a'}])
        with self.assertRaises(ValueError):reel.parse_feed(data,2)
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom</title><summary>Hello</summary><link href="https://source.example/c"/></entry></feed>'
        self.assertEqual(reel.parse_feed(atom,1)[0]['title'],'Atom')

    def test_rss1_rdf_default_and_explicit_namespaces(self):
        data = b'''<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/">
          <channel rdf:about="https://rss.orf.at/news.xml"><title>News</title></channel>
          <item rdf:about="https://news.example/a"><title>One</title><description>Source text</description><link>https://news.example/a?tracking=x</link></item>
          <item rdf:about="https://news.example/b"><title>Two</title><description>Second text</description><link>https://news.example/b</link></item>
        </rdf:RDF>'''
        items = reel.parse_feed(data, 2)
        self.assertEqual(items[0], {'title': 'One', 'text': 'Source text', 'url': 'https://news.example/a'})
        self.assertEqual(items[1]['title'], 'Two')
        prefixed = b'''<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rss="http://purl.org/rss/1.0/">
          <rss:item><rss:title>One</rss:title><rss:description>Source text</rss:description><rss:link>https://news.example/a</rss:link></rss:item>
        </rdf:RDF>'''
        self.assertEqual(reel.parse_feed(prefixed, 1), items[:1])
        with self.assertRaisesRegex(ValueError, 'fewer usable'):
            reel.parse_feed(data, 3)

    def test_prepare_fixture_never_fetches_live_news(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(reel,'read_feed',side_effect=AssertionError('network')):
            config=request();config['test_mode']=True
            reel.prepare(config,Path(directory))
            plan=json.loads((Path(directory)/'plan.json').read_text())
            self.assertIn('technische Testsendung',plan['entries'][0]['title'])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_real_vertical_composition_archives_and_labels_without_repository_write(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);work=root/'work';out=root/'out';config=request();config['test_mode']=True
            reel.prepare(config,work)
            Image.new('RGB',(512,512),'blue').save(work/'studio.png')
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=green:s=256x256:r=25','-t','0.5','-c:v','libx264',str(work/'talking-host.mp4')],check=True)
            with wave.open(str(work/'speech.wav'),'wb') as voice:
                voice.setparams((1,2,16000,0,'NONE','not compressed'));voice.writeframes(b'\0\0'*8000)
            plan=json.loads((work/'plan.json').read_text());plan.update(duration=.5,segments=[{'title':'Testmeldung','start':0,'end':.5}]);(work/'plan.json').write_text(json.dumps(plan))
            video=reel.compose(work,out)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-of','json',str(video)]))
            stream=next(s for s in probe['streams'] if s['codec_type']=='video')
            self.assertEqual((stream['width'],stream['height']),(720,1280))
            self.assertRegex(str(video.relative_to(out)),r'^\d{4}/\d{2}/\d{2}/chat-reel\.mp4$')
            card=Image.open(work/'card-0.png')
            self.assertEqual(card.getpixel((545,1225)),(180,0,0,255))
            manifest=json.loads((out/'manifest.json').read_text());self.assertEqual(manifest['ai_label'],'bottom-right');self.assertFalse(manifest['repository_commit'])


if __name__ == '__main__':unittest.main()
