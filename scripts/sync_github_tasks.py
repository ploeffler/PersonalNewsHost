#!/usr/bin/env python3
"""Idempotent one-way mirror: authoritative JSON tasks -> GitHub issues/milestones.

Authentication uses gh (GH_TOKEN in Actions or the user's existing gh login).
No client leases, secrets, code branches, releases or wiki pages are mutated.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import quote

try:
    from .task_client import validate
except ImportError:
    from task_client import validate

ROOT=Path(__file__).resolve().parents[1]
BRANCH='Full-featured-Newsoutlet'
START='<!-- personalnewshost-managed:start -->'
END='<!-- personalnewshost-managed:end -->'
TASK_MARKER=re.compile(r'<!-- personalnewshost-task:(T\d{3}) -->')
MANAGED='newsoutlet-task'
RECONCILE='needs-reconciliation'


class GitHub:
    def __init__(self,repo,delay=1.3):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise ValueError('Invalid repository')
        self.repo,self.delay,self.writes=repo,delay,0

    def request(self,method,path,body=None):
        args=['gh','api','--method',method,'repos/'+self.repo+'/'+path]
        if body is not None:args+=['--input','-']
        # Never blindly retry a POST: its outcome could be ambiguous. A rerun
        # rediscovers existing task markers before creating anything else.
        result=subprocess.run(args,input=json.dumps(body) if body is not None else None,capture_output=True,text=True)
        if result.returncode:raise RuntimeError('GitHub request failed for '+method+' '+path+'; rerun safely after resolving access/rate limits')
        if method!='GET':
            self.writes+=1
            time.sleep(self.delay)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def list(self,path):
        items=[];page=1
        while True:
            sep='&' if '?' in path else '?'
            batch=self.request('GET',f'{path}{sep}per_page=100&page={page}')
            items.extend(batch)
            if len(batch)<100:return items
            page+=1


def managed_labels(board):
    labels={MANAGED:('315b87','Machine-readable Newsoutlet task'),RECONCILE:('d97706','Uncommitted local implementation must first be reconciled')}
    for status in ['todo','in_progress','review','done','blocked']:
        labels['status:'+status]=({'done':'1a7f37','review':'8250df','blocked':'cf222e'}.get(status,'6e7781'),'Task status mirrored from planning/task-board.json')
    for package in board['packages']:labels['package:'+package['id']]=('0969da',package['title'][:100])
    return labels


def issue_body(task,repo):
    base='https://github.com/'+repo+'/blob/'+BRANCH+'/'
    lines=[f'<!-- personalnewshost-task:{task["id"]} -->',START,
        '**Automatisch aus dem Aufgabenbestand gespiegelt.** Änderungen an Status, Version und Abnahmekriterien erfolgen im JSON-Aufgabenbestand; menschliche Ergänzungen außerhalb dieses Blocks bleiben erhalten.',
        '',f'- **Task:** `{task["id"]}`',f'- **Version:** `{task["version"]}`',f'- **Paket:** `{task["package"]}`',f'- **Status:** `{task["status"]}`',
        f'- **Branch:** `{BRANCH}`',f'- **Verbindlicher Bestand:** [task-board.json]({base}planning/task-board.json)',f'- **Ursprüngliche Aufgabenquelle:** [{task["source"]}]({base}{quote(task["source"],safe="/")})']
    if task.get('local_work_pending'):lines+=['','**Vor Bearbeitung abstimmen:** Hier bestehen noch lokale, nicht vollständig integrierte 0.1-Arbeiten. Nicht unabhängig neu beginnen.']
    lines+=['','### Voraussetzungen','']
    for dep in task['depends_on']:
        query=quote('is:issue in:title "['+dep+']"',safe='')
        lines.append(f'- [{dep}](https://github.com/{repo}/issues?q={query})')
    if not task['depends_on']:lines.append('Keine Aufgaben-Vorgänger.')
    lines+=['','### Umsetzung','']+[f'- {text}' for text in task['instructions']]
    lines+=['','### Abnahmekriterien','']+[('- [x] ' if task['status']=='done' else '- [ ] ')+text for text in task['acceptance']]
    if task.get('evidence'):
        lines+=['','### Bisherige Nachweise','']+[f'- `{value}`' for value in task['evidence']]
    if task.get('implementation_note'):lines+=['',task['implementation_note']]
    lines+=['','### Zusammenarbeit','',
        'Aufgabe über `scripts/task_client.py` übernehmen, Schreibbereiche deklarieren, Tests nachweisen und unabhängig prüfen lassen. GitHub-Assignees oder ein geschlossenes Issue ersetzen keine Lease oder Versionsabnahme.',
        f'[Client-Protokoll]({base}planning/client-protocol.json)',END]
    return '\n'.join(lines)+'\n'


def merge_body(existing,generated):
    if not existing:return generated
    if START in existing and END in existing and existing.index(START)<existing.index(END):
        before=existing[:existing.index(START)];after=existing[existing.index(END)+len(END):]
        block=generated[generated.index(START):generated.index(END)+len(END)]
        return before+block+after
    if TASK_MARKER.search(existing):
        # A marker identifies our issue, but don't overwrite human text on migration.
        return existing.rstrip()+'\n\n'+generated[generated.index(START):]
    raise ValueError('Refusing to overwrite unmanaged issue body')


def sync(api,board,project,progress=print):
    validate(board)
    if any(not re.fullmatch(r'T\d{3}',task['id']) for task in board['tasks']):raise ValueError('Unsupported task ID format')
    if project['branch']!=BRANCH or board['branch']!=BRANCH:raise ValueError('Unexpected source branch')
    desired_labels=managed_labels(board)
    labels={item['name']:item for item in api.list('labels')}
    for name,(color,description) in desired_labels.items():
        if name not in labels:labels[name]=api.request('POST','labels',{'name':name,'color':color,'description':description})
    progress('Labels ready: '+str(len(desired_labels)))
    milestones={item['title']:item for item in api.list('milestones?state=all')}
    completed=set(project['release_policy'].get('completed',[]))
    for release in board['releases']:
        title=release['version']
        description=f'<!-- personalnewshost-release:{title} -->\n{release["title"]}\n\nAbnahme: {release["acceptance"]}\n\nDer JSON-Aufgabenbestand ist maßgeblich. Geschlossene Issues allein bestätigen keinen Versionsabschluss.'
        state='closed' if title in completed and all(t['status']=='done' for t in board['tasks'] if t['version']==title) else 'open'
        old=milestones.get(title)
        if old is None:old=api.request('POST','milestones',{'title':title,'description':description,'state':state})
        elif old.get('description')!=description or old.get('state')!=state:
            old=api.request('PATCH',f'milestones/{old["number"]}',{'description':description,'state':state})
        milestones[title]=old
    progress('Milestones ready: '+str(len(board['releases'])))
    indexed={}
    for item in api.list('issues?state=all'):
        if 'pull_request' in item:continue
        marker=TASK_MARKER.search(item.get('body') or '')
        title_id=re.match(r'^\[(T\d{3})\]',item.get('title') or '')
        if not marker and title_id and title_id.group(1) in {task['id'] for task in board['tasks']}:
            raise ValueError('Existing task title lacks its management marker; reconcile instead of duplicating')
        if marker:
            if marker.group(1) in indexed:raise ValueError('Duplicate managed task issues; manual reconciliation required')
            indexed[marker.group(1)]=item
    mapping={'schema_version':1,'repository':api.repo,'branch':BRANCH,'source_revision':board['revision'],
        'milestones':{v['version']:{'number':milestones[v['version']]['number'],'url':milestones[v['version']].get('html_url','')} for v in board['releases']},'tasks':{}}
    for index,task in enumerate(board['tasks'],1):
        ident=task['id'];old=indexed.get(ident)
        title=f'[{ident}] {task["title"]}'
        labels=[MANAGED,'package:'+task['package'],'status:'+task['status']]
        if task.get('local_work_pending'):labels.append(RECONCILE)
        target_state='closed' if task['status']=='done' else 'open'
        milestone=milestones[task['version']]['number']
        generated=issue_body(task,api.repo)
        if old is None:
            old=api.request('POST','issues',{'title':title,'body':generated,'labels':labels,'milestone':milestone})
            indexed[ident]=old
        body=merge_body(old.get('body'),generated)
        current_labels=[x['name'] if isinstance(x,dict) else x for x in old.get('labels',[])]
        # Preserve labels not owned by this mirror.
        keep=[name for name in current_labels if name!=MANAGED and name!=RECONCILE and not name.startswith(('package:','status:'))]
        wanted_labels=sorted(set(keep+labels));patch={}
        if old.get('title')!=title:patch['title']=title
        if (old.get('body') or '')!=body:patch['body']=body
        if sorted(current_labels)!=wanted_labels:patch['labels']=wanted_labels
        old_milestone=old.get('milestone')
        if (old_milestone.get('number') if isinstance(old_milestone,dict) else old_milestone)!=milestone:patch['milestone']=milestone
        if old.get('state')!=target_state:
            patch.update(state=target_state,state_reason='completed' if target_state=='closed' else 'reopened')
        if patch:old=api.request('PATCH',f'issues/{old["number"]}',patch)
        mapping['tasks'][ident]={'number':old['number'],'url':old.get('html_url',''),'milestone':milestone}
        if index%10==0 or index==len(board['tasks']):progress(f'Tasks mirrored: {index}/{len(board["tasks"])}')
    return mapping


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',default='ploeffler/PersonalNewsHost')
    parser.add_argument('--board',type=Path,default=ROOT/'planning/task-board.json')
    parser.add_argument('--project',type=Path,default=ROOT/'planning/project.json')
    parser.add_argument('--output',type=Path,default=ROOT/'planning/github-task-map.json')
    parser.add_argument('--delay',type=float,default=1.3,help='Seconds after each mutation; default avoids bulk creation bursts')
    args=parser.parse_args()
    if args.delay<0:parser.error('Delay must not be negative')
    board=json.loads(args.board.read_text());project=json.loads(args.project.read_text())
    api=GitHub(args.repo,args.delay)
    mapping=sync(api,board,project,progress=lambda message:print(message,flush=True))
    args.output.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Mirror complete; writes:',api.writes,flush=True)


if __name__=='__main__':main()
