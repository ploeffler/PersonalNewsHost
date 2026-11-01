import json
from pathlib import Path
import tempfile
import threading
import unittest
from scripts.sender_style import Store, Conflict, DEFAULT, normalize, seed, effective_style
from scripts.style_preview import policy


class SenderStyleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'private')
    def test_seed_allowlist_and_compatibility(self):
        config={'title':'Wiesenfunk','editorial_identity':{'format_description':'Lokales','tone':'Ruhig','audience':'Nachbarn'},'secret_name':'DO_NOT_COPY','token':'private-fixture'}
        result=seed(config)
        self.assertEqual(result['name'],'Wiesenfunk');self.assertEqual(result['audience'],'Nachbarn')
        self.assertNotIn('private-fixture',json.dumps(result));self.assertEqual(seed({})['language'],'de')
    def test_invalid_draft_never_changes_active_or_revision(self):
        self.store.adopt(0,policy({}));before=self.store.state()
        for patch in ({'colors':['red']},{'name':''},{'size':'8k'},{'api_key':'not-allowed'}, {'name':'x'*121}):
            with self.assertRaises(ValueError):self.store.save_draft({**DEFAULT,**patch},0)
        self.assertEqual(self.store.state(),before)
    def test_compare_and_swap_preserves_concurrent_draft(self):
        results=[]
        def edit(name):
            try:self.store.save_draft({**DEFAULT,'name':name},0);results.append('saved')
            except Conflict:results.append('conflict')
        threads=[threading.Thread(target=edit,args=(str(i),)) for i in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertCountEqual(results,['saved','conflict'])
    def test_adoption_idempotent_and_restart_preserves_series(self):
        self.store.save_draft({**DEFAULT,'name':'Bergblick'},0)
        first=self.store.adopt(1,policy({}));second=self.store.adopt(1,policy({}))
        self.assertEqual(first,second);self.assertEqual(len(first['batches']),1)
        self.assertEqual(len(first['batches'][0]['jobs']),14)
        self.assertEqual(Store(self.store.root).state(),first)
        self.assertEqual(self.store.path.stat().st_mode&0o777,0o600)
        self.assertEqual(self.store.root.stat().st_mode&0o777,0o700)
    def test_version_history_immutable_and_restore_is_draft_only(self):
        first=self.store.adopt(0,policy({}));old=first['active_version']
        self.store.save_draft({**DEFAULT,'name':'Neue CI'},0);second=self.store.adopt(1,policy({}))
        self.assertNotEqual(second['active_version'],old)
        self.assertTrue(any(batch['stale'] for batch in second['batches']))
        restored=self.store.restore(old,1)
        self.assertEqual(restored['draft']['name'],DEFAULT['name'])
        self.assertEqual(restored['active_version'],second['active_version'])
        oldjob=next(b for b in restored['batches'] if b['version']==old)['jobs'][0]
        context=json.loads(self.store.job_context(oldjob['id'])['snapshot'])
        self.assertEqual(context['style']['name'],DEFAULT['name'])
    def test_recovery_requires_explicit_uncertain_retry(self):
        state=self.store.adopt(0,policy({}));job=state['batches'][0]['jobs'][0]['id']
        with self.store.db() as db:db.execute("UPDATE jobs SET status='processing' WHERE id=?",(job,))
        self.store.recover();self.assertEqual(self.store.job_context(job)['status'],'uncertain')
        with self.assertRaises(ValueError):self.store.retry(job)
        self.store.retry(job,True);self.assertEqual(self.store.job_context(job)['status'],'queued')
    def test_snapshot_rejects_unexpected_provider_fields(self):
        with self.assertRaises(ValueError):self.store.adopt(0,{**policy({}),'credentials':'forbidden'})
    def test_effective_style_does_not_mutate_snapshot(self):
        snapshot={'version':'v1','style':normalize(DEFAULT)}
        result=effective_style(snapshot,{'tone':'Lebhaft'})
        self.assertEqual(result['style']['tone'],'Lebhaft');self.assertEqual(snapshot['style']['tone'],DEFAULT['tone'])
        self.assertIsNone(effective_style(None))
    def test_sources_bounded_and_credentials_rejected(self):
        with self.assertRaises(ValueError):normalize({**DEFAULT,'sources':[{'url':'https://site.example/?token=fixture','retrieved_at':1}]})
        with self.assertRaises(ValueError):normalize({**DEFAULT,'sources':[{'url':'http://127.0.0.1','retrieved_at':1}]})

    def test_recovery_reuses_durable_image_without_second_provider_attempt(self):
        from PIL import Image
        state=self.store.adopt(0,policy({}));job=state['batches'][0]['jobs'][0]['id']
        images=self.store.root/'images';images.mkdir();Image.new('RGB',(1536,1024)).save(images/(job+'.png'))
        with self.store.db() as db:db.execute("UPDATE jobs SET status='processing',attempts=1 WHERE id=?",(job,))
        self.store.recover();result=self.store.job_context(job)
        self.assertEqual(result['status'],'complete');self.assertEqual(result['attempts'],1)
