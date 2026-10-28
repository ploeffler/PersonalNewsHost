"""No live Telegram messages; all network calls are mocked."""
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
import unittest
import urllib.parse
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('short_telegram', Path(__file__).resolve().parents[1] / 'scripts/publish_short_updates_telegram.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ShortTelegramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        self.queue = self.root / 'queue.json'
        self.now = 2000000
        self.env = {'TELEGRAM_BOT_TOKEN': 'fake-secret', 'TELEGRAM_CHAT_ID': 'first',
                    'TELEGRAM_CHAT_ID_SECONDARY': 'second'}
        self.config = {'telegram': {'enabled': True, 'target': 'secondary'}}
        self.updates = [{'id': 'a' * 24, 'title': 'Neue Entwicklung', 'text': 'Die Reform wurde beschlossen.',
                         'source': 'example.org', 'url': 'https://example.org/story',
                         'created_at': self.now - 10}]
        self.save()
        self.network = patch('urllib.request.urlopen', side_effect=lambda *a, **k: io.StringIO('{"ok":true,"result":{"message_id":1}}'))
        self.http = self.network.start()
        self.addCleanup(self.network.stop)

    def save(self):
        (self.root / 'config.json').write_text(json.dumps(self.config))
        (self.root / 'docs/short-updates.json').write_text(json.dumps({'updates': self.updates}))

    def prepare(self): m.prepare(self.root, self.queue, self.env, self.now)
    def send(self): m.deliver(self.root, self.queue, self.env, self.now)

    def test_secondary_and_repeat_across_runs(self):
        self.prepare();self.http.assert_not_called();self.send()
        request = self.http.call_args.args[0]
        data = urllib.parse.parse_qs(request.data.decode())
        self.assertEqual(data['chat_id'], ['second'])
        self.assertIn(self.updates[0]['text'], data['text'][0])
        self.assertIn('https://example.org/story', data['text'][0])
        self.assertIn('/short-updates.html', data['text'][0])
        self.assertNotIn('parse_mode', data)
        self.prepare();self.send()
        self.http.assert_called_once()
        self.assertNotIn('fake-secret', (self.root / '.state/short-update-telegram.json').read_text())
        self.assertNotIn('chat_id', (self.root / '.state/short-update-telegram.json').read_text())
        self.assertIn('secondary:16367aacb67a4a01/', (self.root / '.state/short-update-telegram.json').read_text())

    def test_same_queue_cannot_be_sent_twice(self):
        self.prepare();self.send();self.send();self.http.assert_called_once()

    def test_timeout_does_not_retry_and_hides_token(self):
        self.prepare()
        self.http.side_effect = TimeoutError('https://api.telegram.org/botfake-secret/sendMessage')
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors), self.assertRaises(RuntimeError): self.send()
        self.assertNotIn('fake-secret', errors.getvalue())
        self.prepare();self.send();self.http.assert_called_once()

    def test_disabled_and_old_updates(self):
        for disabled in [{'telegram': {'enabled': False}}, {'telegram': {'enabled': True}, 'short_updates': {'telegram_enabled': False}}]:
            self.config = disabled;self.save();self.prepare();self.send()
        self.http.assert_not_called()
        self.config = {'telegram': {'enabled': True}}
        self.updates[0]['created_at'] = self.now - 3600
        self.save();self.prepare();self.send();self.http.assert_not_called()

    def test_missing_credentials_does_not_reserve(self):
        self.env.pop('TELEGRAM_BOT_TOKEN')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse((self.root / '.state/short-update-telegram.json').exists())
        self.http.assert_not_called()

    def test_destination_change_refuses_send(self):
        self.prepare();self.env['TELEGRAM_CHAT_ID_SECONDARY'] = 'new-chat'
        with self.assertRaises(ValueError): self.send()
        self.http.assert_not_called()

    def test_future_updates_and_invalid_ids(self):
        self.updates[0]['created_at'] = self.now + 1
        self.save();self.prepare();self.send()
        self.updates[0]['created_at'] = self.now - 1;self.updates[0]['id'] = '../bad'
        self.save();self.prepare();self.send();self.http.assert_not_called()

    def test_unicode_and_long_text_fit_telegram(self):
        update = {**self.updates[0], 'text': '😀' * 5000}
        text = m.message(update, 'https://example.org/')
        self.assertLessEqual(len(text.encode('utf-16-le')) // 2, 4096)
        self.assertIn('https://example.org/story', text)

    def test_rejected_api_result_fails(self):
        self.prepare();self.http.side_effect = lambda *a, **k: io.StringIO('{"ok":false}')
        with self.assertRaises(RuntimeError):self.send()

if __name__ == '__main__': unittest.main()
