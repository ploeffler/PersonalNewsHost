"""Shared runtime entry points without GitHub context or provider credentials."""
from contextlib import redirect_stdout, redirect_stderr
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from scripts import local_runtime as runtime

ROOT = Path(__file__).resolve().parents[1]


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = runtime.layout(self.root)
        self.config = json.loads((ROOT / 'config.example.json').read_text())
        self.config.pop('shows', None)
        self.config['providers'] = []
        self.config['automation'] = {'enabled': False, 'timezone': 'Europe/Vienna'}
        self.path = self.root / 'config.json'
        self.path.write_text(json.dumps(self.config))

    def test_container_and_checkout_share_relative_paths(self):
        container = runtime.layout('/app')
        for key, path in self.paths.items():
            self.assertEqual(path.relative_to(self.root), container[key].relative_to('/app'))
        self.assertNotEqual(self.paths['public'], self.paths['productions'])
        self.assertNotIn(self.paths['state'], self.paths['public'].parents)

    def test_due_uses_show_settings_without_github_manual_override(self):
        with patch.dict('os.environ', {'GITHUB_EVENT_NAME': 'workflow_dispatch'}, clear=True):
            result = runtime.due(self.path, 'main', self.paths,
                                 dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc))
        self.assertFalse(result['due'])
        self.assertEqual(result['timezone'], 'Europe/Vienna')
        self.assertFalse(self.paths['productions'].exists())

    def test_produce_delegates_to_existing_isolated_production_without_publishing(self):
        with patch('scripts.produce_show.produce', return_value=self.paths['productions'] / 'main') as produce:
            runtime.produce(self.path, 'main', self.paths)
        self.assertEqual(produce.call_args.args[1:], ('main', self.paths['productions']))

    def test_invalid_config_rejected_before_producer(self):
        self.path.write_text('{"title": false}')
        with patch('scripts.produce_show.produce') as produce:
            with self.assertRaises(ValueError):
                runtime.produce(self.path, 'main', self.paths)
        produce.assert_not_called()

    def test_preview_binds_loopback_and_only_public_directory(self):
        self.paths['public'].mkdir(parents=True)
        server = MagicMock()
        with patch.object(runtime, 'ThreadingHTTPServer', return_value=server) as factory:
            runtime.preview(self.paths, 8080)
        self.assertEqual(factory.call_args.args[0], ('127.0.0.1', 8080))
        self.assertEqual(factory.call_args.args[1].keywords['directory'], str(self.paths['public']))
        server.__enter__.return_value.serve_forever.assert_called_once()

    def test_preview_rejects_symlinks_and_privileged_ports_before_binding(self):
        self.paths['public'].mkdir(parents=True)
        with patch.object(runtime, 'ThreadingHTTPServer') as server:
            with self.assertRaises(ValueError): runtime.preview(self.paths, 443)
            (self.paths['public'] / 'private').symlink_to(self.root)
            with self.assertRaises(ValueError): runtime.preview(self.paths, 8080)
        server.assert_not_called()

    def test_inspect_does_not_read_config_or_environment_secrets(self):
        output = io.StringIO()
        with patch.dict('os.environ', {'API_SECRET': 'private-fixture-value'}), redirect_stdout(output):
            self.assertEqual(runtime.main(['inspect', '--config', '/missing/config.json']), 0)
        self.assertNotIn('private-fixture-value', output.getvalue())
        self.assertFalse(json.loads(output.getvalue())['publishes_automatically'])

    def test_cli_failure_is_redacted(self):
        output = io.StringIO()
        with redirect_stderr(output):
            self.assertEqual(runtime.main(['produce', '--config', str(self.root / 'private-value.json')]), 1)
        self.assertNotIn('private-value', output.getvalue())
