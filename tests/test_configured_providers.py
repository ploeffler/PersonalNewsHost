"""Offline contracts for configured providers and the executable gateway."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.configured_providers import ProviderRegistry
from scripts.provider_runtime import KINDS, ProviderAuth, ProviderQuota, ProviderRejected, ProviderTimeout
from scripts.validate_config import validate_config

ROOT = Path(__file__).resolve().parents[1]


class ConfiguredProvidersTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = json.loads((ROOT / 'config.example.json').read_text())
        self.config.pop('shows', None)

    def registry(self, config=None, **kwargs):
        return ProviderRegistry(config or self.config, self.temp.name, **kwargs)

    def test_all_six_kinds_execute_deterministic_mock_fixtures_offline(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')), patch('socket.getaddrinfo', side_effect=AssertionError('network forbidden')):
            first = self.registry()
            self.assertEqual({s['kind'] for s in self.config['providers']}, KINDS)
            for kind in sorted(KINDS):
                payload = {'text': 'Quellenauszug', 'title': 'Meldung', 'source_id': 's1', 'prompt': 'Studio', 'audio_ref': 'local.wav'}
                a = first.run(kind, payload)
                b = self.registry().run(kind, payload)
                self.assertEqual(a['value'], b['value'])
                self.assertTrue(b['cached'])
                self.assertFalse(a['cached'])
                self.assertFalse(first.runtime.providers[a['provider_id']].paid)
                if kind in {'text_analysis', 'text_generation'}:
                    self.assertEqual(a['value'], {'text': 'Quellenauszug', 'source_ids': ['s1']})
                else:
                    self.assertEqual(a['value']['status'], 'mock')

    def test_priority_and_explicit_selection_are_stable(self):
        extra = copy.deepcopy(self.config['providers'][0]);extra.update(id='preferred', priority=1)
        self.config['providers'].append(extra)
        registry = self.registry()
        self.assertEqual(registry.run('text_generation', {'text': 'x'})['provider_id'], 'preferred')
        self.assertEqual(registry.run('text_generation', {'text': 'x'}, provider_id='mock-text-generation')['provider_id'], 'mock-text-generation')

    def test_disabled_unknown_and_wrong_kind_never_execute(self):
        self.config['providers'][0]['enabled'] = False
        registry = self.registry()
        for ident in ['mock-text-generation', 'missing', 'mock-tts']:
            with self.assertRaises(ValueError):registry.run('text_generation', {'text': 'x'}, provider_id=ident)
        self.assertNotIn('mock-text-generation', registry.runtime.providers)

    def test_invalid_config_rejected_before_cache_creation(self):
        for change in ['duplicate', 'cycle', 'missing', 'kind', 'disabled', 'endpoint', 'adapter', 'cost', 'timeout', 'retries']:
            with self.subTest(change=change):
                c = copy.deepcopy(self.config);a=c['providers'][0];b=c['providers'][1]
                if change == 'duplicate':c['providers'].append(copy.deepcopy(a))
                if change == 'cycle':a['fallback_to']=a['id']
                if change == 'missing':a['fallback_to']='missing'
                if change == 'kind':a['fallback_to']=b['id']
                if change == 'disabled':
                    other=copy.deepcopy(a);other.update(id='disabled',enabled=False);c['providers'].append(other);a['fallback_to']='disabled'
                if change == 'endpoint':a['endpoint']='https://remote.invalid'
                if change == 'adapter':a['adapter']='remote'
                if change == 'cost':a['cost_model']['max_cost_eur']=1
                if change == 'timeout':a['timeout_s']=0
                if change == 'retries':a['retries']=4
                with self.assertRaises(ValueError):self.registry(c)

    def test_typed_errors_follow_configured_fallback_chain(self):
        for error in [ProviderTimeout, ProviderQuota, ProviderAuth, ProviderRejected]:
            with self.subTest(error=error):
                c=copy.deepcopy(self.config);a=c['providers'][0];b=copy.deepcopy(a);d=copy.deepcopy(a)
                b['id']='second';d['id']='third';a['fallback_to']='second';b['fallback_to']='third';c['providers'] += [b,d]
                r=self.registry(c)
                with patch.object(r.runtime.providers[a['id']], 'generate', side_effect=error('redacted')) as primary, patch.object(r.runtime.providers['second'], 'generate', side_effect=error('redacted')):
                    result=r.run('text_generation',{'text':error.__name__})
                self.assertEqual(result['provider_id'],'third');self.assertEqual(primary.call_count,1)

    def test_timeout_options_retries_and_model_reach_interface(self):
        spec=self.config['providers'][0];spec.update(timeout_s=7,retries=1,model='fixture-revision')
        r=self.registry();provider=r.runtime.providers[spec['id']];original=provider.generate
        count=[]
        def attempt(request, *, timeout_s):
            count.append(timeout_s);self.assertEqual(request.model,'fixture-revision')
            if len(count)==1:raise ProviderTimeout('simulated')
            return original(request,timeout_s=timeout_s)
        with patch.object(provider,'generate',side_effect=attempt):r.run('text_generation',{'text':'x'})
        self.assertEqual(count,[7,7])

    def test_rate_limit_uses_fallback_and_recovers_after_window(self):
        a=self.config['providers'][0];b=copy.deepcopy(a);b.update(id='backup',priority=200);a.update(rate_limit=1,fallback_to='backup');self.config['providers'].append(b)
        now=[0];r=self.registry(clock=lambda:now[0])
        self.assertEqual(r.run('text_generation',{'text':'one'})['provider_id'],a['id'])
        self.assertEqual(r.run('text_generation',{'text':'two'})['provider_id'],'backup')
        now[0]=60
        self.assertEqual(r.run('text_generation',{'text':'three'})['provider_id'],a['id'])

    def test_retries_count_as_attempts_and_cache_hits_do_not(self):
        a=self.config['providers'][0];b=copy.deepcopy(a)
        b.update(id='backup',priority=200);a.update(rate_limit=1,retries=1,fallback_to='backup')
        self.config['providers'].append(b);r=self.registry()
        with patch.object(r.runtime.providers[a['id']],'generate',side_effect=ProviderTimeout('deadline')) as primary:
            self.assertEqual(r.run('text_generation',{'text':'retry'})['provider_id'],'backup')
            self.assertEqual(primary.call_count,1)
        r=self.registry()
        self.assertFalse(r.run('text_generation',{'text':'cached'})['cached'])
        self.assertTrue(r.run('text_generation',{'text':'cached'})['cached'])
        self.assertEqual(len(r.calls[a['id']]),1)

    def test_unit_quota_survives_registry_restart_and_uses_fallback(self):
        primary = self.config['providers'][0]
        backup = copy.deepcopy(primary)
        backup.update(id='quota-backup', priority=200)
        primary['fallback_to'] = backup['id']
        primary['cost_model']['units'] = {'tokens': 2}
        self.config['providers'].append(backup)
        self.config['provider_budgets']['unit_limits'] = {'tokens': 2}
        first = self.registry()
        self.assertEqual(first.run('text_generation', {'text': 'one'})['provider_id'], primary['id'])
        second = self.registry()
        self.assertEqual(second.run('text_generation', {'text': 'two'})['provider_id'], backup['id'])
        self.assertEqual(second.runtime.providers[primary['id']].calls, 0)

    def test_cache_hit_does_not_reserve_units_again(self):
        primary = self.config['providers'][0]
        primary['cost_model']['units'] = {'tokens': 2}
        self.config['provider_budgets']['unit_limits'] = {'tokens': 2}
        first = self.registry()
        first.run('text_generation', {'text': 'same'})
        second = self.registry()
        self.assertTrue(second.run('text_generation', {'text': 'same'})['cached'])
        usage = second.runtime.budget.summary(second.runtime.namespace, second.runtime.run_id)
        self.assertEqual(usage['providers'], {})
        with self.assertRaises(ProviderQuota):
            second.run('text_generation', {'text': 'different'})

    def test_retry_reserves_units_before_each_attempt(self):
        primary = self.config['providers'][0]
        primary.update(retries=1)
        primary['cost_model']['units'] = {'tokens': 2}
        self.config['provider_budgets']['unit_limits'] = {'tokens': 2}
        registry = self.registry()
        with patch.object(registry.runtime.providers[primary['id']], 'generate',
                          side_effect=ProviderTimeout('simulated')) as generate:
            with self.assertRaises(ProviderQuota):
                registry.run('text_generation', {'text': 'retry-unit-quota'})
        self.assertEqual(generate.call_count, 1)

    def test_registry_writes_usage_without_payload_to_workflow_summary(self):
        summary = Path(self.temp.name) / 'summary.md'
        with patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': str(summary)}):
            registry = self.registry()
            registry.run('text_generation', {'text': 'private-fixture-content'})
        report = summary.read_text()
        self.assertIn('mock-text-generation', report)
        self.assertIn('reserved_eur', report)
        self.assertNotIn('private-fixture-content', report)

    def test_mocks_never_resolve_environment_secrets(self):
        self.config['providers'][0]['secret_name']='SOME_API_KEY'
        with patch('os.getenv',side_effect=AssertionError('must not resolve secret')):
            self.registry().run('text_generation',{'text':'x'})

    def test_cli_invokes_registry_and_redacts_failures(self):
        path=Path(self.temp.name)/'config.json';path.write_text(json.dumps(self.config))
        args=[sys.executable,str(ROOT/'scripts/run_provider.py'),'--config',str(path),'--kind','tts','--state',self.temp.name]
        ok=subprocess.run(args,input=json.dumps({'text':'hello'}),capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr);self.assertEqual(json.loads(ok.stdout)['value']['status'],'mock')
        bad=subprocess.run(args,input='private-invalid-json',capture_output=True,text=True)
        self.assertNotEqual(bad.returncode,0);self.assertNotIn('private-invalid-json',bad.stderr)

    def test_configuration_validation_checks_fallback_semantics(self):
        self.config['providers'][0]['fallback_to']='does-not-exist'
        with self.assertRaisesRegex(ValueError,'fallback'):validate_config(self.config)


if __name__ == '__main__':unittest.main()
