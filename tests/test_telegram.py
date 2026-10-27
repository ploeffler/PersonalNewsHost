"""Offline Telegram contracts: network calls are always mocked."""
import datetime as dt
import hashlib
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

    def test_secondary_and_cleanup(self):
        self.run_script('publish_telegram.py')
        self.assertIn(b'chat_id=second', self.http.call_args.args[0].data)
        ledger = self.root / 'telegram_sent.json'
        entries = json.loads(ledger.read_text())
        self.assertEqual(entries[0]['target'], 'secondary')
        self.assertEqual(entries[0]['chat_hash'], hashlib.sha256(b'second').hexdigest())
        self.http.reset_mock()
        self.run_script('cleanup_telegram.py')
        self.http.assert_not_called()
        entries[0]['sent_at'] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=25, seconds=1)).isoformat()
        ledger.write_text(json.dumps(entries))
        self.run_script('cleanup_telegram.py')
        self.assertIn(b'chat_id=second', self.http.call_args.args[0].data)
        self.assertEqual(json.loads(ledger.read_text()), [])

    def test_changed_destination_is_not_deleted(self):
        self.run_script('publish_telegram.py')
        ledger = self.root / 'telegram_sent.json'
        entries = json.loads(ledger.read_text())
        entries[0]['sent_at'] = '2026-01-01T00:00:00+00:00'
        ledger.write_text(json.dumps(entries))
        os.environ['TELEGRAM_CHAT_ID_SECONDARY'] = 'changed'
        self.http.reset_mock()
        self.run_script('cleanup_telegram.py')
        self.http.assert_not_called()
        self.assertEqual(json.loads(ledger.read_text()), entries)

    def test_no_expiry(self):
        self.config['telegram']['auto_delete'] = False
        self.run_script('publish_telegram.py')
        self.assertFalse((self.root / 'telegram_sent.json').exists())

    def test_missing_video_and_corrupt_ledger_block_send(self):
        (self.root / 'docs/latest.mp4').unlink()
        with self.assertRaises(SystemExit):
            self.run_script('publish_telegram.py')
        self.http.assert_not_called()
        (self.root / 'docs/latest.mp4').write_bytes(b'fixture')
        (self.root / 'telegram_sent.json').write_text('broken')
        with self.assertRaises(ValueError):
            self.run_script('publish_telegram.py')
        self.http.assert_not_called()

    def test_disabled(self):
        self.config['telegram']['enabled'] = False
        with self.assertRaises(SystemExit) as result:
            self.run_script('publish_telegram.py')
        self.assertEqual(result.exception.code, 0)
        self.http.assert_not_called()
