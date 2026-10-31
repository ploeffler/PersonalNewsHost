"""T104 acceptance: adapter-boundary allowlists and private content-free audit."""
from dataclasses import replace
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from scripts.provider_runtime import Cache, FIELDS, MockProvider, ProviderRejected, Request, Runtime


class PayloadAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = Runtime(Cache(self.root / 'cache.sqlite'), secret_values=['configured-private-value'])

    def test_all_six_adapter_boundaries_receive_only_allowlisted_scalars(self):
        for kind, allowed in FIELDS.items():
            with self.subTest(kind=kind):
                provider = MockProvider(kind, kind)
                self.runtime.register(provider)
                payload = {field: (1 if field == 'duration_seconds' else 'public-fixture') for field in allowed}
                payload.update(config={'secret': 'discarded-private-data'}, tools=['shell'], system='discarded')
                request = Request(kind, 'fixture', 'mock-v1', 'v1', payload)
                with patch.object(provider, 'generate', wraps=provider.generate) as generate:
                    self.runtime.run(kind, request)
                sent = generate.call_args.args[0].payload
                self.assertEqual(set(sent), allowed)
                self.assertNotIn('discarded-private-data', json.dumps(sent))
                row = json.loads(self.runtime.audit_path.read_text().splitlines()[-1])
                self.assertEqual(set(row), {'provider', 'kind', 'task', 'bytes', 'at'})
                self.assertEqual(row['bytes'], len(json.dumps(sent, sort_keys=True, ensure_ascii=False,
                                                            separators=(',', ':')).encode()))

    def test_audit_is_private_before_first_write_and_contains_no_content(self):
        provider = MockProvider('mock', 'text_generation')
        self.runtime.register(provider)
        request = Request('text_generation', 'summary', 'mock-v1', 'v1', {'text': 'private-fixture-content'})
        original = os.fchmod
        def verify(fd, mode):
            self.assertEqual(stat.S_IMODE(os.fstat(fd).st_mode), 0o600)
            self.assertEqual(os.fstat(fd).st_size, 0)
            return original(fd, mode)
        with patch('scripts.provider_runtime.os.fchmod', side_effect=verify):
            self.runtime.run('mock', request)
        self.assertNotIn('private-fixture-content', self.runtime.audit_path.read_text())
        self.assertEqual(stat.S_IMODE(self.runtime.audit_path.stat().st_mode), 0o600)
        self.runtime.audit_path.chmod(0o644)
        self.runtime.run('mock', replace(request, payload={'text': 'second'}))
        self.assertEqual(stat.S_IMODE(self.runtime.audit_path.stat().st_mode), 0o600)
        self.runtime.run('mock', request)
        self.assertEqual(len(self.runtime.audit_path.read_text().splitlines()), 2)

    def test_secrets_stop_before_adapter_cache_and_audit(self):
        provider = MockProvider('mock', 'text_generation')
        self.runtime.register(provider)
        values = ['configured-private-value', 'Bearer fixture-credential',
                  'gh' + 'p_' + 'a' * 36, 'github' + '_pat_' + 'b' * 50,
                  'sk-' + 'proj-' + 'c' * 24]
        for value in values:
            with self.subTest(format=value.split('_')[0]):
                request = Request('text_generation', 'summary', 'mock-v1', 'v1', {'text': value})
                with self.assertRaises(ProviderRejected):
                    self.runtime.run('mock', request)
        self.assertEqual(provider.calls, 0)
        self.assertFalse(self.runtime.audit_path.exists())

    def test_audit_symlink_is_rejected_before_adapter_execution(self):
        target = self.root / 'untouched.txt'
        target.write_text('unchanged')
        self.runtime.audit_path.symlink_to(target)
        provider = MockProvider('mock', 'tts')
        self.runtime.register(provider)
        with self.assertRaises(OSError):
            self.runtime.run('mock', Request('tts', 'fixture', 'mock-v1', 'v1', {'text': 'public'}))
        self.assertEqual(provider.calls, 0)
        self.assertEqual(target.read_text(), 'unchanged')

    def test_payload_content_cannot_be_used_as_audit_metadata(self):
        provider = MockProvider('mock', 'tts')
        self.runtime.register(provider)
        with self.assertRaises(ValueError):
            self.runtime.run('mock', Request('tts', 'private message as task', 'm', 'v1', {}))
        with self.assertRaises(ValueError):
            self.runtime.register(MockProvider('provider\nprivate message', 'tts'))
        self.assertFalse(self.runtime.audit_path.exists())
