from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from scripts.provider_budget import Budget, BudgetExceeded
from scripts.configured_providers import configured_analysis_runtime, analyze_entries
from scripts.provider_runtime import Request, ProviderQuota
from scripts.analysis_tasks import SCHEMAS
from scripts.validate_config import validate_config
import json


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'usage.sqlite'

    def test_zero_budget_blocks_cost(self):
        budget=Budget(self.path)
        with self.assertRaises(BudgetExceeded):budget.reserve('app','run','mock','0.01')
        budget.reserve('app','run','mock',0)

    def test_concurrent_reservations_never_exceed_month(self):
        budget=Budget(self.path,monthly_budget_eur='0.03',per_run_budget_eur=1)
        def reserve(i):
            try:budget.reserve('app',str(i),'mock','0.01');return True
            except BudgetExceeded:return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve,range(8))),3)

    def test_restart_and_month_rollover(self):
        budget=Budget(self.path,monthly_budget_eur=1,per_run_budget_eur=1)
        budget.reserve('app','first','mock',1,now=datetime(2026,10,1,tzinfo=timezone.utc))
        restored=Budget(self.path,monthly_budget_eur=1,per_run_budget_eur=1)
        with self.assertRaises(BudgetExceeded):restored.reserve('app','second','mock',1,now=datetime(2026,10,30,tzinfo=timezone.utc))
        restored.reserve('app','second','mock',1,now=datetime(2026,11,1,tzinfo=timezone.utc))

    def test_units_and_rate_limit(self):
        budget=Budget(self.path,unit_limits={'tokens':5})
        budget.reserve('app','r','mock',0,{'tokens':5})
        with self.assertRaises(BudgetExceeded):budget.reserve('app','r','mock',0,{'tokens':1})
        budget.reserve('app','r','limited',0,rate_limit=1)
        with self.assertRaises(BudgetExceeded):budget.reserve('app','r','limited',0,rate_limit=1)

    def test_configured_cost_fallback_and_cache(self):
        config={'providers':[{'id':'paid-mock','kind':'text_analysis','enabled':True,'cost_model':{'max_cost_eur':0.01},'fallback_to':'free'},
                             {'id':'free','kind':'text_analysis','enabled':True}],
                'provider_budgets':{'allow_paid':True,'monthly_budget_eur':0.01,'per_run_budget_eur':0.01}}
        runtime,specs=configured_analysis_runtime(config,self.temp.name,run_id='r')
        req=Request('text_analysis','summary','mock','v1',{'text':'Fact','source_id':'a'})
        first=runtime.run('paid-mock',req,fallback_to='free')
        self.assertEqual(first['provider_id'],'paid-mock')
        self.assertTrue(runtime.run('paid-mock',req)['cached'])
        req=Request('text_analysis','summary','mock','v1',{'text':'Another','source_id':'b'})
        self.assertEqual(runtime.run('paid-mock',req,fallback_to='free')['provider_id'],'free')
        summary=runtime.budget.summary(runtime.namespace,'r')
        self.assertEqual(summary['providers']['paid-mock']['reserved_eur'],'0.01')
        audit=(Path(self.temp.name)/'audit.jsonl').read_text()
        self.assertNotIn('Another',audit)
        self.assertNotIn('Fact',audit)

    def test_seven_schemas_and_repeat_without_calls(self):
        config={'providers':[{'id':'analysis','kind':'text_analysis','enabled':True}],
                'provider_tasks':{task:'analysis' for task in SCHEMAS}}
        output=Path(self.temp.name)/'analysis.json'
        entries=[('Title','Public source text.','https://example.org/1',[])]
        analyze_entries(config,entries,self.temp.name,output)
        self.assertEqual(len(json.loads(output.read_text())['results']),7)
        analyze_entries(config,entries,self.temp.name,output)
        self.assertTrue(all(r['cached'] for r in json.loads(output.read_text())['results']))

    def test_paid_opt_in_required(self):
        config={'providers':[{'id':'p','kind':'text_analysis','enabled':True,'cost_model':{'max_cost_eur':1}}],
                'provider_budgets':{'monthly_budget_eur':10,'per_run_budget_eur':10}}
        runtime,_=configured_analysis_runtime(config,self.temp.name)
        with self.assertRaises(ProviderQuota):runtime.run('p',Request('text_analysis','summary','m','v1',{}))
        self.assertEqual(runtime.providers['p'].calls,0)

    def test_fallback_cycles_rejected(self):
        cfg={'title':'Test','feeds':[],'providers':[{'id':'a','kind':'tts','enabled':True,'fallback_to':'b'},
                                                              {'id':'b','kind':'tts','enabled':True,'fallback_to':'a'}]}
        with self.assertRaises(ValueError):validate_config(cfg)
