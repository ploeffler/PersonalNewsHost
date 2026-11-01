"""T135: hostile feed data cannot select tasks, schemas, tools or output paths."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.analysis_tasks import SCHEMAS, baseline
from scripts.provider_runtime import Cache, InvalidResponse, MockProvider, Request, Runtime

FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'provider-injection.json'


class FeedInjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = Runtime(Cache(self.root / 'cache.sqlite'))
        self.provider = MockProvider('analysis', 'text_analysis')
        self.runtime.register(self.provider)
        self.hostile = json.loads(FIXTURE.read_text())

    def test_hostile_feed_keeps_caller_task_schema_and_allowed_data_for_all_tasks(self):
        allowed = {key: self.hostile[key] for key in ('title', 'text', 'source_id')}
        for task in SCHEMAS:
            with self.subTest(task=task):
                request = Request('text_analysis', task, 'mock-v1', 'v1', self.hostile)
                with patch('subprocess.run', side_effect=AssertionError('tool execution forbidden')), \
                     patch('os.system', side_effect=AssertionError('shell execution forbidden')), \
                     patch.object(self.provider, 'generate', wraps=self.provider.generate) as generate:
                    result = self.runtime.run('analysis', request)
                received = generate.call_args.args[0]
                self.assertEqual(received.task, task)
                self.assertEqual(received.payload, allowed)
                self.assertEqual(result['value'], baseline(task, allowed))
                self.assertNotIn('command', result['value'])
        self.assertFalse((self.root / 'PNH_INJECTION_SENTINEL').exists())
        self.assertFalse(Path('PNH_INJECTION_SENTINEL').exists())
        self.assertNotIn('Ignore previous instructions', self.runtime.audit_path.read_text())

    def test_tool_shaped_provider_output_is_rejected_for_each_task(self):
        for task in SCHEMAS:
            with self.subTest(task=task):
                with patch.object(self.provider, 'generate', return_value={'command': 'execute', 'tools': ['shell']}):
                    with self.assertRaises(InvalidResponse):
                        self.runtime.run('analysis', Request('text_analysis', task, 'mock-v1', 'v1', self.hostile))

    def test_instruction_like_text_remains_inert_source_data(self):
        # Source text can quote hostile instructions. The extractive mock returns
        # that quotation verbatim, without interpreting or executing it.
        request = Request('text_analysis', 'summary', 'mock-v1', 'v1', self.hostile)
        result = self.runtime.run('analysis', request)
        self.assertEqual(result['value']['text'], self.hostile['text'])
        self.assertEqual(result['value']['source_ids'], [self.hostile['source_id']])
        repeated = self.runtime.run('analysis', request)
        self.assertTrue(repeated['cached'])
        self.assertEqual(self.provider.calls, 1)
