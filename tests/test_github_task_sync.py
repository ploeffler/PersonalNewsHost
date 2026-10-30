from copy import deepcopy
import unittest
from scripts.sync_github_tasks import sync,START,END
from test_task_client import board


class FakeGitHub:
    repo='owner/repo'
    def __init__(self):self.data={'labels':[],'milestones':[],'issues':[]};self.writes=[]
    def list(self,path):return deepcopy(self.data[path.split('?')[0]])
    def request(self,method,path,body):
        self.writes.append((method,path,deepcopy(body)));kind=path.split('/')[0]
        if method=='POST':
            item={'number':len(self.data[kind])+1,'html_url':'https://example.invalid/item','state':'open','body':'',**deepcopy(body)}
            self.data[kind].append(item);return deepcopy(item)
        item=next(x for x in self.data[kind] if x['number']==int(path.split('/')[1]));item.update(deepcopy(body));return deepcopy(item)


class GitHubTaskSyncTests(unittest.TestCase):
    def test_create_and_repeat_without_duplicate_or_mutation(self):
        api=FakeGitHub();source=board();project={'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}}
        first=sync(api,source,project,progress=lambda _:None)
        count=len(api.writes);second=sync(api,source,project,progress=lambda _:None)
        self.assertEqual(first,second);self.assertEqual(len(api.writes),count)
        self.assertEqual(len(api.data['issues']),2);self.assertEqual(len(api.data['milestones']),1)

    def test_human_notes_and_unmanaged_labels_are_preserved(self):
        api=FakeGitHub();source=board();project={'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}}
        sync(api,source,project,progress=lambda _:None)
        api.data['issues'][0]['body']+='\nHuman note.';api.data['issues'][0]['labels'].append('custom')
        source['tasks'][0]['title']='New title'
        sync(api,source,project,progress=lambda _:None)
        self.assertIn('Human note.',api.data['issues'][0]['body']);self.assertIn('custom',api.data['issues'][0]['labels'])

    def test_done_closes_issue_but_not_milestone(self):
        api=FakeGitHub();source=board();source['tasks'][0]['status']='done'
        project={'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}}
        sync(api,source,project,progress=lambda _:None)
        self.assertEqual(api.data['issues'][0]['state'],'closed')
        self.assertEqual(api.data['milestones'][0]['state'],'open')
        source['tasks'][0]['status']='todo';sync(api,source,project,progress=lambda _:None)
        self.assertEqual(api.data['issues'][0]['state'],'open')

    def test_ambiguous_create_is_recovered_without_duplicate(self):
        class Interrupted(FakeGitHub):
            failed=False
            def request(self,method,path,body):
                result=super().request(method,path,body)
                if method=='POST' and path=='issues' and not self.failed:
                    self.failed=True
                    raise RuntimeError('Network response lost after successful create')
                return result
        api=Interrupted();source=board();project={'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}}
        with self.assertRaises(RuntimeError):sync(api,source,project,progress=lambda _:None)
        self.assertEqual(len(api.data['issues']),1)
        sync(api,source,project,progress=lambda _:None)
        self.assertEqual(len(api.data['issues']),2)

    def test_task_title_collision_without_marker_is_not_duplicated(self):
        api=FakeGitHub();api.data['issues']=[{'number':1,'title':'[T001] Existing human issue','body':'Notes','labels':[],'state':'open'}]
        with self.assertRaises(ValueError):sync(api,board(),{'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}},progress=lambda _:None)
        self.assertEqual(len(api.data['issues']),1)

    def test_duplicate_managed_issues_fail(self):
        api=FakeGitHub();source=board();project={'branch':'Full-featured-Newsoutlet','release_policy':{'completed':[]}}
        sync(api,source,project,progress=lambda _:None)
        api.data['issues'].append(deepcopy(api.data['issues'][0]))
        with self.assertRaises(ValueError):sync(api,source,project,progress=lambda _:None)
