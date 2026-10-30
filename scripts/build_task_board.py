#!/usr/bin/env python3
"""Import planning sources once into an explicit multi-client development board."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

ROOT=Path(__file__).resolve().parents[1]

# Explicit gates previously only stated in the narrative plan.
EXTRA={
 'T120':['T135'],'T115':['T125','T133','T134'],'T122':['T102'],
 'T125':['T132'],'T131':['T120'],'T032':['T022'],'T040':['T020'],
 'T144':['T103'],'T166':['T103'],'T143':['T142','T144','T145'],
 'T152':['T125','T133','T162','T167'],'T153':['T125','T133'],
 'T214':['T215'],'T291':['T292'],'T252':['T253','T254','T255'],
 'T254':['T270'],'T255':['T270'],
}


def load(path):return yaml.safe_load(path.read_text(encoding='utf-8'))


def build(root=ROOT):
 root=Path(root);plan=load(root/'planning/arbeitspakete.yaml');versions=load(root/'planning/versionen-0.1-bis-1.0.yaml');progress=load(root/'planning/fortschritt.yaml')
 tasks={};digests={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['planning/arbeitspakete.yaml','planning/versionen-0.1-bis-1.0.yaml','planning/fortschritt.yaml']}
 for source in plan['meta']['sources']:
  path=(root/'planning'/source).resolve();rel=path.relative_to(root).as_posix()
  digests[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
  for task in load(path).get('tasks',[]):
   if task['id'] in tasks:raise ValueError('Duplicate task ID')
   tasks[task['id']]={**deepcopy(task),'source':rel}
 by_release={i:v['version'] for v in versions['releases'] for i in v['tasks']}
 by_package={i:p['id'] for p in plan['packages'] for i in p['tasks']}
 assert set(tasks)==set(by_release)==set(by_package)
 completed={t['id']:t for t in progress['completed']}
 pending={t['id']:t for t in progress['in_progress']}
 local={'T001','T012','T072','T073','T100','T101','T103','T104','T130','T135'}
 # Snapshot contains implementation work outside committed history; never promote it.
 for ident,t in tasks.items():
  for field in ('instructions','acceptance'):
   t[field]=[x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,sort_keys=True) for x in t[field]]
  t['depends_on']=sorted(set(t['depends_on']+EXTRA.get(ident,[])))
  t.update(version=by_release[ident],package=by_package[ident],
           status='done' if ident in completed else 'in_progress' if ident in pending or ident in local else 'todo',
           lease=None,review=None,local_work_pending=ident in local,
           evidence=completed.get(ident,pending.get(ident,{})).get('evidence',[]),
           implementation_note=completed.get(ident,{}).get('note',''),
           coordination_note='Uncommitted local 0.1 work must be reconciled before another client claims this task.' if ident in local else '')
  if isinstance(t['evidence'],str):t['evidence']=[t['evidence']]
 # Apply explicit user overrides to historical imported tasks.
 tasks['T110']['instructions'].append('staff-Rechte beschreiben virtuelle Workflowfähigkeiten; keine individuellen Mitarbeiterkonten. Verwaltung direkt im Ressort.')
 tasks['T128']['instructions'].insert(0,'Freigaben primär im gemeinsamen Redaktionsarbeitskorb; optionale Benachrichtigungen ersetzen diesen nicht.')
 tasks['T030']['instructions']=[s for s in tasks['T030']['instructions'] if 'entfernen' not in s and 'Aufbewahrung' not in s]
 tasks['T030']['instructions'].append('Archivvideos niemals automatisch löschen. Pflichtarchiv unter Jahr/Monat/Tag gemäß T260; Bereinigung nur für temporäre Dateien/Caches.')
 tasks['T030']['acceptance']=[s for s in tasks['T030']['acceptance'] if 'entfernt' not in s]+['Archivvideos bleiben dauerhaft erhalten; temporäre Dateien werden getrennt verwaltet.']
 # Full release acceptance includes every planned task, including later supplements.
 tasks['T081']['depends_on']=sorted(set(tasks)-{'T081'})
 remaining=set(tasks);done=set();layers=[]
 number=lambda v:tuple(int(n) for n in v.split('.'))
 while remaining:
  layer=sorted(i for i in remaining if set(tasks[i]['depends_on'])<=done)
  if not layer:raise ValueError('Dependency cycle or unknown ID')
  layers.append(layer);done.update(layer);remaining.difference_update(layer)
 for ident,t in tasks.items():
  if any(number(tasks[d]['version'])>number(t['version']) for d in t['depends_on']):raise ValueError('Dependency targets later release: '+ident)
 board={'schema_version':1,'revision':0,'active_version':progress['meta']['active_version'],
        'branch':'Full-featured-Newsoutlet','tasks':list(tasks.values()),
        'packages':[{'id':p['id'],'title':p['title'],'tasks':p['tasks']} for p in plan['packages']],
        'releases':[{'version':v['version'],'title':v['title'],'tasks':v['tasks'],'acceptance':v['exit_criteria']} for v in versions['releases']],
        'source_sha256':digests,'dependency_layers':layers,'events':[]}
 return board


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=ROOT/'planning/task-board.json')
 args=parser.parse_args()
 if args.output.exists():parser.error('Refusing to overwrite live coordination state; import updates deliberately')
 board=build();args.output.write_text(json.dumps(board,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(len(board['tasks']),'tasks,',len(board['packages']),'packages;',len(board['releases']),'releases')


if __name__=='__main__':main()
