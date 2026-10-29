"""Offline Telegram contracts: network calls are always mocked."""
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]

class TelegramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'docs').mkdir()
        for name in ('publish_telegram.py', 'cleanup_telegram.py'):
            (self.root / 'scripts' / name).write_text((SOURCE / 'scripts' / name).read_text())
        self.config = {'telegram': {'enabled': True, 'delivery': 'link', 'target': 'secondary'}}
        (self.root / 'docs/latest.mp4').write_bytes(b'offline fixture')
        self.env = patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'fake', 'TELEGRAM_CHAT_ID': 'first', 'TELEGRAM_CHAT_ID_SECONDARY': 'second'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.network = patch('urllib.request.urlopen', side_effect=lambda *a, **k: io.StringIO(json.dumps({'ok': True, 'result': {'message_id': 7}})))
        self.http = self.network.start()
        self.addCleanup(self.network.stop)

    def run_script(self, name):
        (self.root / 'config.json').write_text(json.dumps(self.config))
        runpy.run_path(str(self.root / 'scripts' / name), run_name='__main__')

    def test_secondary(self):
        self.run_script('publish_telegram.py')
        self.assertIn(b'chat_id=second', self.http.call_args.args[0].data)
        self.assertFalse((self.root / 'telegram_sent.json').exists())

    def test_video_caption_lists_broadcast_topics_in_order(self):
        self.config['telegram']['delivery'] = 'video'
        self.config['telegram']['caption'] = '{title}\n{url}'
        (self.root / 'docs/story-groups.json').write_text(json.dumps([
            {'headline': 'Erstes Thema'}, {'headline': 'Zweites\nThema'}]))
        with self.assertRaises(SystemExit) as result:
            self.run_script('publish_telegram.py')
        self.assertEqual(result.exception.code, 0)
        request = self.http.call_args.args[0]
        self.assertTrue(request.full_url.endswith('/sendVideo'))
        self.assertIn('Themen:\n• Erstes Thema\n• Zweites Thema', request.data.decode())
        self.assertIn('latest.mp4', request.data.decode())

    def test_long_caption_and_emoji_topics_fit_telegram_limit(self):
        self.config['telegram']['caption'] = 'X' * 2000
        (self.root / 'docs/story-groups.json').write_text(json.dumps([
            {'headline': str(i) + '😀' * 500} for i in range(5)]))
        self.run_script('publish_telegram.py')
        from urllib.parse import parse_qs
        caption = parse_qs(self.http.call_args.args[0].data.decode())['text'][0]
        self.assertLessEqual(len(caption.encode('utf-16-le')) // 2, 1024)
        for i in range(5):
            self.assertIn('• ' + str(i), caption)

    def test_invalid_topic_file_preserves_caption(self):
        self.config['telegram']['caption'] = 'Meine Beschriftung'
        (self.root / 'docs/story-groups.json').write_text('invalid json')
        self.run_script('publish_telegram.py')
        from urllib.parse import parse_qs
        caption = parse_qs(self.http.call_args.args[0].data.decode())['text'][0]
        self.assertEqual(caption, 'Meine Beschriftung')

    def test_cleanup_never_calls_telegram(self):
        ledger = self.root / 'telegram_sent.json'
        ledger.write_text('[{"message_id":7,"sent_at":"2020-01-01T00:00:00+00:00"}]')
        original = ledger.read_text()
        self.run_script('cleanup_telegram.py')
        self.http.assert_not_called()
        self.assertEqual(ledger.read_text(), original)

    def test_legacy_deletion_setting_is_ignored(self):
        self.config['telegram']['auto_delete'] = True
        (self.root / 'telegram_sent.json').write_text('legacy data')
        self.run_script('publish_telegram.py')
        self.http.assert_called_once()
        self.assertEqual((self.root / 'telegram_sent.json').read_text(), 'legacy data')

    def test_missing_video_blocks_send(self):
        (self.root / 'docs/latest.mp4').unlink()
        with self.assertRaises(SystemExit):
            self.run_script('publish_telegram.py')
        self.http.assert_not_called()

    def test_disabled(self):
        self.config['telegram']['enabled'] = False
        with self.assertRaises(SystemExit) as result:
            self.run_script('publish_telegram.py')
        self.assertEqual(result.exception.code, 0)
        self.http.assert_not_called()
