"""T103 acceptance: cache identity and durable cross-process cost idempotency."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from scripts.provider_runtime import Cache, MockProvider, Request, Runtime, TEXT_SCHEMA

ROOT = Path(__file__).resolve().parents[1]


class CacheAcceptanceTests(unittest.TestCase):
    def test_canonical_field_order_and_discarded_fields_share_result(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Cache(Path(directory) / 'cache.sqlite'))
            provider = MockProvider('mock', 'text_generation')
            runtime.register(provider)
            request = Request('text_generation', 'summary', 'mock-v1', 'v1',
                              {'text': 'Public text', 'source_id': 's1'})
            runtime.run('mock', request)
            reordered = replace(request, payload={'source_id': 's1', 'text': 'Public text',
                                                  'private_config': {'ignored': True}})
            self.assertTrue(runtime.run('mock', reordered)['cached'])
            self.assertEqual(provider.calls, 1)

    def test_provider_and_response_schema_are_distinct_cache_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Cache(Path(directory) / 'cache.sqlite'))
            for ident in ('one', 'two'):
                runtime.register(MockProvider(ident, 'text_generation'))
            request = Request('text_generation', 'summary', 'mock-v1', 'v1', {'text': 'Fact'})
            runtime.run('one', request)
            self.assertFalse(runtime.run('two', request)['cached'])
            schema = dict(TEXT_SCHEMA, description='A new response contract')
            self.assertFalse(runtime.run('one', request, schema=schema)['cached'])
            self.assertTrue(runtime.run('one', request, schema=schema)['cached'])

    def test_independent_processes_and_restart_reserve_mock_cost_only_once(self):
        worker = '''
import json, sys, time
from pathlib import Path
from scripts.provider_budget import Budget
from scripts.provider_runtime import Cache, MockProvider, Request, Runtime
class MeteredMock(MockProvider):
    paid = True
    billing_verified = True
    max_cost_eur = '0.01'
    def generate(self, request, *, timeout_s):
        time.sleep(0.1)
        return super().generate(request, timeout_s=timeout_s)
state = Path(sys.argv[1])
runtime = Runtime(Cache(state/'cache.sqlite'), budget=Budget(state/'usage.sqlite', monthly_budget_eur=1, per_run_budget_eur=1))
runtime.register(MeteredMock('mock', 'text_generation'))
print(json.dumps(runtime.run('mock', Request('text_generation', 'summary', 'mock-v1', 'v1', {'text':'Public fixture'}))))
'''
        with tempfile.TemporaryDirectory() as directory:
            def run_worker(_):
                result = subprocess.run([sys.executable, '-c', worker, directory], cwd=ROOT,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(run_worker, range(4)))
            self.assertEqual(sum(not result['cached'] for result in results), 1)
            self.assertTrue(run_worker(None)['cached'])
            with sqlite3.connect(Path(directory) / 'usage.sqlite') as db:
                reservations = db.execute('SELECT cost FROM reservations').fetchall()
            self.assertEqual(reservations, [('0.01',)])
