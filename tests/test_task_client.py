from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from jsonschema import Draft202012Validator
from scripts.task_client import GitBoard,Conflict,transition,validate

ROOT=Path(__file__).resolve().parents[1]


def board():
    tasks=[]
    for ident in ['T001','T002']:
        tasks.append({'id':ident,'epic':'E0','title':'Test '+ident,'status':'todo','depends_on':[],
            'instructions':['Implement'],'acceptance':['Verify'],'source':'test.yaml','version':'0.1','package':'A00',
            'lease':None,'review':None,'local_work_pending':False,'evidence':[],'implementation_note':'','coordination_note':''})
    return {'schema_version':1,'revision':0,'active_version':'0.1','branch':'Full-featured-Newsoutlet','tasks':tasks,
            'packages':[{'id':'A00','title':'Test','tasks':['T001','T002']}],
            'releases':[{'version':'0.1','title':'Test','tasks':['T001','T002'],'acceptance':'Pass'}],
            'source_sha256':{},'dependency_layers':[['T001','T002']],'events':[]}


class TaskStateTests(unittest.TestCase):
    def test_project_board_and_schema(self):
        data=json.loads((ROOT/'planning/task-board.json').read_text())
        schema=json.loads((ROOT/'planning/task-board.schema.json').read_text())
        Draft202012Validator(schema).validate(data);validate(data)
        project=json.loads((ROOT/'planning/project.json').read_text())
        self.assertEqual(len(data['tasks']),project['inventory']['task_count'])
        self.assertEqual(len(data['packages']),project['inventory']['package_count'])
        self.assertEqual(len(data['releases']),project['inventory']['release_count'])
        # Local-only holds are temporary; a fully reconciled board is valid.
        self.assertTrue(all(type(t['local_work_pending']) is bool for t in data['tasks']))

    def test_claim_conflict_and_file_scope_conflict(self):
        data,item=transition(board(),'claim','T001','one',files=['scripts/'],now=100)
        with self.assertRaises(Conflict):transition(data,'claim','T001','two',files=['other.py'],now=101)
        with self.assertRaises(Conflict):transition(data,'claim','T002','two',files=['scripts/a.py'],now=101)
        _,other=transition(data,'claim','T002','two',files=['tests/a.py'],now=101)
        self.assertEqual(other['lease']['client'],'two')

    def test_expired_owner_is_fenced(self):
        data,old=transition(board(),'claim','T001','one',files=['a.py'],ttl=60,now=100)
        new,item=transition(data,'claim','T001','two',files=['a.py'],now=161)
        with self.assertRaises(Conflict):transition(new,'submit','T001','one',token=old['lease']['token'],proof={'commit':'a'*40,'checks':'passed'},now=162)
        self.assertEqual(item['lease']['client'],'two')

    def test_dependency_and_local_pending_block(self):
        data=board();data['tasks'][1]['depends_on']=['T001']
        with self.assertRaises(Conflict):transition(data,'claim','T002','two',files=['a.py'])
        data=board();data['tasks'][0]['local_work_pending']=True
        with self.assertRaises(Conflict):transition(data,'claim','T001','one',files=['a.py'])

    def test_review_is_separate_and_requires_evidence(self):
        data,item=transition(board(),'claim','T001','one',files=['a.py'],now=100)
        token=item['lease']['token']
        with self.assertRaises(Conflict):transition(data,'submit','T001','one',token=token,now=101)
        data,item=transition(data,'submit','T001','one',token=token,proof={'commit':'a'*40,'checks':'passed'},now=101)
        with self.assertRaises(Conflict):transition(data,'complete','T001','one',note='self review',now=102)
        data,item=transition(data,'complete','T001','reviewer',note='checked',now=102)
        self.assertEqual(item['status'],'done');self.assertIsNone(item['lease'])

    def test_unsafe_or_empty_scopes_rejected(self):
        for files in [[],['../outside'],['/outside'],['.git/config'],['scripts/*'],['.']]:
            with self.subTest(files=files),self.assertRaises(Conflict):transition(board(),'claim','T001','one',files=files)

    def test_state_input_is_not_mutated(self):
        data=board();copy=deepcopy(data)
        transition(data,'claim','T001','one',files=['a.py'])
        self.assertEqual(data,copy)


class GitCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.remote=self.root/'remote.git';writer=self.root/'writer'
        self.command('git','init','--bare',str(self.remote))
        self.command('git','init',str(writer))
        self.command('git','-C',str(writer),'config','user.name','Test')
        self.command('git','-C',str(writer),'config','user.email','test@example.invalid')
        self.command('git','-C',str(writer),'checkout','-b','Full-featured-Newsoutlet')
        (writer/'planning').mkdir();(writer/'planning/task-board.json').write_text(json.dumps(board()))
        (writer/'original.txt').write_text('Do not modify')
        self.command('git','-C',str(writer),'add','.')
        self.command('git','-C',str(writer),'commit','-m','Initial board')
        self.command('git','-C',str(writer),'remote','add','origin',str(self.remote))
        self.command('git','-C',str(writer),'push','origin','Full-featured-Newsoutlet')
        self.clients=[GitBoard(self.remote,self.root/f'client-{i}.git','Test','test@example.invalid') for i in range(2)]

    def command(self,*args):return subprocess.run(args,check=True,capture_output=True).stdout

    def test_two_clients_cannot_both_claim_same_task(self):
        def claim(pair):
            index,client=pair
            with client.locked():
                try:return client.mutate('claim','T001',f'client-{index}',files=['a.py'])['lease']['client']
                except Conflict:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,enumerate(self.clients)))
        self.assertEqual(sum(r is not None for r in results),1)
        with self.clients[0].locked():
            head,data=self.clients[0].snapshot()
            self.assertEqual(data['revision'],1)
            self.assertEqual(self.clients[0].git('show',head+':original.txt').stdout,b'Do not modify')

    def test_stale_revision_cannot_publish(self):
        a,b=self.clients
        with a.locked():a.mutate('claim','T001','first',files=['a.py'],expected_revision=0)
        with b.locked():
            with self.assertRaises(Conflict):b.mutate('claim','T002','second',files=['b.py'],expected_revision=0)
            result=b.mutate('claim','T002','second',files=['b.py'])
            self.assertEqual(result['lease']['client'],'second')

    def test_non_shared_evidence_commit_is_rejected(self):
        a=self.clients[0]
        with a.locked():
            task=a.mutate('claim','T001','one',files=['a.py'])
            with self.assertRaises(Conflict):a.mutate('submit','T001','one',token=task['lease']['token'],proof={'commit':'a'*40,'checks':'passed'})
