#!/usr/bin/env python3
"""JSON task coordination using ordinary fast-forward Git pushes as compare-and-swap.

This tool changes only planning/task-board.json, never a client's working checkout.
Clients are trusted repository writers, not authenticated product users.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
BRANCH='Full-featured-Newsoutlet'
BOARD='planning/task-board.json'
IDENT=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$')


class Conflict(ValueError): pass


def scope_path(value):
    p=PurePosixPath(value)
    if not value or str(p)=='.' or p.is_absolute() or '..' in p.parts or '.git' in p.parts or '\\' in value or any(c in value for c in '*?[]\n\r\x00'):
        raise Conflict('Write scopes must be explicit relative files or directories')
    return str(p)+('/' if value.endswith('/') else '')


def overlap(a,b):
    return a==b or (a.endswith('/') and b.startswith(a)) or (b.endswith('/') and a.startswith(b))


def validate(board):
    ids=[t['id'] for t in board['tasks']]
    if len(ids)!=len(set(ids)) or board['branch']!=BRANCH:raise Conflict('Invalid board identity')
    known=set(ids);done=set();remaining=set(ids);by={t['id']:t for t in board['tasks']}
    while remaining:
        layer={i for i in remaining if set(by[i]['depends_on'])<=done}
        if not layer:raise Conflict('Dependency graph is invalid')
        done|=layer;remaining-=layer
    listed=[i for release in board['releases'] for i in release['tasks']]
    if len(listed)!=len(ids) or set(listed)!=known:raise Conflict('Incomplete release assignment')
    for release in board['releases']:
        if any(by[ident]['version']!=release['version'] for ident in release['tasks']):raise Conflict('Task release metadata mismatch')
    assigned=[i for package in board['packages'] for i in package['tasks']]
    if len(assigned)!=len(ids) or set(assigned)!=known:raise Conflict('Incomplete package assignment')
    for task in board['tasks']:
        if task['status'] not in {'todo','in_progress','review','done','blocked'}:raise Conflict('Invalid task status')


def ready(board,task):
    done={t['id'] for t in board['tasks'] if t['status']=='done'}
    return task['version']==board['active_version'] and not task.get('local_work_pending') and set(task['depends_on'])<=done and task['status'] in {'todo','in_progress'}


def transition(board,action,task_id,client,*,token=None,files=(),ttl=3600,note='',proof=None,now=None,operation=None):
    if not IDENT.fullmatch(client):raise Conflict('Invalid client ID')
    if len(note)>2000:raise Conflict('Note too long')
    now=time.time() if now is None else now
    result=deepcopy(board);task=next((t for t in result['tasks'] if t['id']==task_id),None)
    if task is None:raise Conflict('Unknown task')
    lease=task.get('lease')
    if action=='claim':
        if not ready(result,task):raise Conflict('Task is not ready in the active version, or has unreconciled local work')
        if lease and lease['expires_at']>now:raise Conflict('Task is already leased')
        files=sorted(set(scope_path(p) for p in files))
        if not files:raise Conflict('Declare intended write files/directories with --file')
        if type(ttl) is not int or not 60<=ttl<=14400:raise Conflict('Lease must be 60–14400 seconds')
        for other in result['tasks']:
            active=other.get('lease')
            if other['id']!=task_id and active and active['expires_at']>now and any(overlap(a,b) for a in files for b in active['files']):
                raise Conflict('Write scope conflicts with another active task')
        task.update(status='in_progress',review=None,lease={'client':client,'token':uuid.uuid4().hex,'expires_at':now+ttl,'files':files})
    elif action in {'heartbeat','release','submit'}:
        if not lease or lease['client']!=client or lease['token']!=token or lease['expires_at']<=now:raise Conflict('Missing, expired or stale lease')
        if action=='heartbeat':
            if not 60<=ttl<=14400:raise Conflict('Invalid lease duration')
            lease['expires_at']=now+ttl
        elif action=='release':task.update(status='todo',lease=None,review=None)
        else:
            if not proof or not proof.get('commit') or not proof.get('checks'):raise Conflict('Submit requires committed work and check evidence')
            task.update(status='review',review={'author':client,'commit':proof['commit'],'checks':proof['checks'],'files':lease['files']})
    elif action in {'complete','reject'}:
        review=task.get('review')
        if task['status']!='review' or not review or review['author']==client:raise Conflict('An independent client must review submitted work')
        if not note:raise Conflict('Review note required')
        if action=='complete':task.update(status='done',lease=None,review={**review,'reviewer':client,'decision':note},evidence=[review['commit'],review['checks']])
        else:task.update(status='todo',lease=None,review={**review,'reviewer':client,'rejected':note})
    elif action=='reconcile':
        if not task.get('local_work_pending') or not proof or not proof.get('commit') or not note:raise Conflict('Reconcile requires local work, a committed integration and a note')
        task.update(local_work_pending=False,status='todo',lease=None,coordination_note=note,evidence=list(task.get('evidence',[]))+[proof['commit']])
    else:raise Conflict('Unknown transition')
    result['revision']+=1
    result['events'].append({'operation_id':operation or uuid.uuid4().hex,'revision':result['revision'],'action':action,'task':task_id,'client':client,'at':now,'note':note})
    validate(result)
    return result,task


class GitBoard:
    def __init__(self,remote,cache,author_name,author_email):
        self.remote,self.cache,self.name,self.email=str(remote),Path(cache),author_name,author_email

    def git(self,*args,input=None,check=True):
        command=['git','--git-dir',str(self.cache),'-c','user.name='+self.name,'-c','user.email='+self.email,*args]
        p=subprocess.run(command,input=input,capture_output=True)
        if check and p.returncode:raise Conflict('Git coordination failed; no task ownership confirmed')
        return p

    @contextmanager
    def locked(self):
        self.cache.parent.mkdir(parents=True,exist_ok=True)
        with self.cache.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if not self.cache.exists():
                subprocess.run(['git','init','--bare',str(self.cache)],check=True,capture_output=True)
                self.git('remote','add','origin',self.remote)
            yield

    def snapshot(self):
        self.git('fetch','--quiet','origin','refs/heads/'+BRANCH)
        head=self.git('rev-parse','FETCH_HEAD').stdout.decode().strip()
        board=json.loads(self.git('show',head+':'+BOARD).stdout)
        validate(board);return head,board

    def replace_tree(self,tree,name,sha,mode,kind):
        entries=[e for e in self.git('ls-tree','-z',tree).stdout.split(b'\0') if e]
        entries=[e for e in entries if e.split(b'\t',1)[1].decode()!=name]
        entries.append(f'{mode} {kind} {sha}\t{name}'.encode())
        return self.git('mktree','-z',input=b'\0'.join(entries)+b'\0').stdout.decode().strip()

    def commit_board(self,head,board):
        data=(json.dumps(board,ensure_ascii=False,indent=2)+'\n').encode()
        blob=self.git('hash-object','-w','--stdin',input=data).stdout.decode().strip()
        planning=self.replace_tree(head+':planning','task-board.json',blob,'100644','blob')
        root=self.replace_tree(head,'planning',planning,'040000','tree')
        return self.git('commit-tree',root,'-p',head,'-m','coord: '+board['events'][-1]['action']+' '+board['events'][-1]['task']).stdout.decode().strip()

    def mutate(self,action,task,client,*,expected_revision=None,**kwargs):
        operation=uuid.uuid4().hex
        for attempt in range(4):
            head,board=self.snapshot()
            if any(e['operation_id']==operation for e in board['events']):return next(t for t in board['tasks'] if t['id']==task)
            if expected_revision is not None and board['revision']!=expected_revision:raise Conflict('Board revision changed; fetch and reconsider')
            proof=kwargs.get('proof')
            if proof and proof.get('commit'):
                if not re.fullmatch('[0-9a-f]{40}',proof['commit']) or self.git('merge-base','--is-ancestor',proof['commit'],head,check=False).returncode:
                    raise Conflict('Evidence commit must already exist on the shared development branch')
            if action=='complete':
                item=next((t for t in board['tasks'] if t['id']==task),None)
                review=item.get('review') if item else None
                if review and self.git('diff','--name-only',review['commit'],head,'--',*review['files']).stdout.strip():
                    raise Conflict('Submitted files changed after check evidence; resubmit required')
            updated,result=transition(board,action,task,client,operation=operation,**kwargs)
            commit=self.commit_board(head,updated)
            # No --force. A concurrent branch update rejects the push atomically.
            if self.git('push','--quiet','origin',commit+':refs/heads/'+BRANCH,check=False).returncode==0:return result
        raise Conflict('Remote contention or network failure; no ownership confirmed, inspect board')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['list','show','claim','heartbeat','release','submit','complete','reject','reconcile'])
    parser.add_argument('--task');parser.add_argument('--client',required=True)
    parser.add_argument('--remote');parser.add_argument('--cache',type=Path)
    parser.add_argument('--token');parser.add_argument('--file',action='append',default=[])
    parser.add_argument('--ttl',type=int,default=3600);parser.add_argument('--expected-revision',type=int)
    parser.add_argument('--note',default='');parser.add_argument('--commit');parser.add_argument('--checks')
    args=parser.parse_args()
    if not IDENT.fullmatch(args.client):parser.error('Invalid client ID')
    def config(key):
        p=subprocess.run(['git','-C',str(ROOT),'config','--get',key],capture_output=True,text=True)
        if p.returncode:parser.error('Configure Git '+key+' first')
        return p.stdout.strip()
    remote=args.remote or subprocess.check_output(['git','-C',str(ROOT),'remote','get-url','origin'],text=True).strip()
    store=GitBoard(remote,args.cache or ROOT/'.test-tmp/task-clients'/(args.client+'.git'),config('user.name'),config('user.email'))
    try:
        with store.locked():
            if args.action in {'list','show'}:
                head,board=store.snapshot()
                values=[t for t in board['tasks'] if t['id']==args.task] if args.action=='show' else [t for t in board['tasks'] if ready(board,t)]
                print(json.dumps({'head':head,'revision':board['revision'],'active_version':board['active_version'],'tasks':values,'local_work_pending':[t['id'] for t in board['tasks'] if t.get('local_work_pending')]},ensure_ascii=False,indent=2))
            else:
                if not args.task:parser.error('--task required')
                result=store.mutate(args.action,args.task,args.client,expected_revision=args.expected_revision,
                    token=args.token,files=args.file,ttl=args.ttl,note=args.note,
                    proof={'commit':args.commit,'checks':args.checks} if args.commit else None)
                print(json.dumps(result,ensure_ascii=False,indent=2))
    except (Conflict,OSError,ValueError) as exc:parser.exit(1,str(exc)+'\n')


if __name__=='__main__':main()
