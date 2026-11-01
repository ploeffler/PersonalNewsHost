"""T130: strict output contracts, retries and fallbacks for every analysis task."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from scripts.analysis_tasks import SCHEMAS, baseline
from scripts.provider_runtime import Cache, InvalidResponse, MockProvider, Request, Runtime


class AnalysisContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Runtime(Cache(Path(self.temp.name) / 'cache.sqlite'))
        self.primary = MockProvider('primary', 'text_analysis')
        self.fallback = MockProvider('fallback', 'text_analysis')
        self.runtime.register(self.primary)
        self.runtime.register(self.fallback)
        self.payload = {'title': 'Public title', 'text': 'Public fact.', 'source_id': 's1'}

    def request(self, task):
        return Request('text_analysis', task, 'mock-v1', 'analysis-v1', self.payload)

    def test_all_seven_baselines_match_their_strict_contracts(self):
        self.assertEqual(set(SCHEMAS), {'summary', 'entities', 'classification', 'relevance',
                                       'bias', 'duplicates', 'headline'})
        for task, schema in SCHEMAS.items():
            with self.subTest(task=task):
                Draft202012Validator.check_schema(schema)
                result = self.runtime.run('primary', self.request(task))
                Draft202012Validator(schema).validate(result['value'])
                self.assertEqual(result['value'], baseline(task, self.payload))

    def test_each_task_retries_invalid_response_then_caches_valid_response(self):
        for task in SCHEMAS:
            with self.subTest(task=task):
                valid = baseline(task, self.payload)
                with patch.object(self.primary, 'generate', side_effect=[{'unexpected': True}, valid]) as generate:
                    self.assertEqual(self.runtime.run('primary', self.request(task), retries=1)['value'], valid)
                    self.assertEqual(generate.call_count, 2)
                    self.assertTrue(self.runtime.run('primary', self.request(task))['cached'])
                    self.assertEqual(generate.call_count, 2)

    def test_each_task_rejects_invalid_response_and_uses_separate_fallback(self):
        for task in SCHEMAS:
            with self.subTest(task=task):
                with patch.object(self.primary, 'generate', return_value={'command': 'execute'}) as generate:
                    result = self.runtime.run('primary', self.request(task), retries=1, fallback_to='fallback')
                    self.assertEqual(result['provider_id'], 'fallback')
                    self.assertEqual(generate.call_count, 2)
                    with self.assertRaises(InvalidResponse):
                        self.runtime.run('primary', self.request(task))
                    self.assertEqual(generate.call_count, 3)

    def test_missing_extra_nested_wrong_type_and_nonfinite_outputs_are_rejected(self):
        invalid = {
            'summary': [{'text': 'missing sources'}, {'text': 1, 'source_ids': []},
                        {'text': 'x', 'source_ids': [], 'tools': ['shell']}],
            'entities': [{'entities': [{'text': 'x', 'type': 'unsupported'}]},
                         {'entities': [{'text': 'x', 'type': 'person', 'command': 'shell'}]}],
            'classification': [{'category': ['politics']}],
            'relevance': [{'score': -1}, {'score': 2}, {'score': True}, {'score': float('nan')}],
            'bias': [{'note': 'unverified', 'assessed': True}],
            'duplicates': [{'candidate_ids': [1], 'assessed': False}],
            'headline': [{'text': 'x' * 1001}],
        }
        for task, values in invalid.items():
            for index, value in enumerate(values):
                with self.subTest(task=task, case=index), patch.object(self.primary, 'generate', return_value=value):
                    with self.assertRaises(InvalidResponse):
                        self.runtime.run('primary', self.request(task))

    def test_nested_schema_mutation_does_not_turn_invalid_response_into_cache_hit(self):
        schema = copy.deepcopy(SCHEMAS['entities'])
        self.runtime.run('primary', self.request('entities'), schema=schema)
        schema['properties']['entities']['minItems'] = 1
        with self.assertRaises(InvalidResponse):
            self.runtime.run('primary', self.request('entities'), schema=schema)
