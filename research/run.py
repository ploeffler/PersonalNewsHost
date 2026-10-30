#!/usr/bin/env python3
"""Run one research group and export validated, reviewable results as artifacts."""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
try:
    from .validate_catalogs import ROOT,validate
except ImportError:
    from validate_catalogs import ROOT,validate

GROUPS={
    'news':{
        'steps':['research/rss/collect.py','research/rss/supplement.py','research/rss/build_catalog.py'],
        'builder':'research/rss/build_catalog.py',
        'files':['docs/feed-catalog.json','docs/feed-catalog.opml','docs/guide/rss-quellenliste.md','research/rss/feed-research-raw.json'],
    },
    'authorities':{
        'steps':['research/police-rss/discover.py','research/police-rss/collect.py','research/police-rss/collect_emergency.py','research/police-rss/build_catalog.py'],
        'builder':'research/police-rss/build_catalog.py',
        'files':['docs/police-feed-catalog.json','docs/police-feed-catalog.opml','docs/guide/polizei-rss-quellenliste.md','research/police-rss/discovery.json','research/police-rss/checks.json','research/police-rss/emergency-checks.json'],
    },
}

def run_group(group,output,offline=False,root=ROOT):
    output=Path(output).resolve()
    # Keep failed attempts from exporting a previous run's successful files.
    output.mkdir(parents=True,exist_ok=False)
    manifest={'group':group,'mode':'stored_snapshot' if offline else 'live','status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
    manifest_path=output/'manifest.json'
    def save():
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    save()
    try:
        with (output/'run.log').open('w',encoding='utf-8') as log:
            steps=[GROUPS[group]['builder']] if offline else GROUPS[group]['steps']
            for script in steps:
                print(f'[Research] {group}: {script}',flush=True)
                log.write(f'\n$ python {script}\n');log.flush()
                result=subprocess.run([sys.executable,'-B',script],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=False)
                log.write(result.stdout);log.flush()
                print(result.stdout,end='',flush=True)
                result.check_returncode()
        manifest['validation']=validate(group,root)
        # Export only after every stage and validation succeeded. On failure,
        # the artifact contains the failure manifest and log, not stale catalogues.
        for relative in GROUPS[group]['files']:
            destination=output/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/relative,destination)
        manifest['status']='success'
    except Exception as exc:
        manifest['status']='failed'
        manifest['error']=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        manifest['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
        save()
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group',choices=GROUPS,required=True)
    parser.add_argument('--output-dir',type=Path,required=True,help='New artifact directory; existing directories are refused')
    parser.add_argument('--offline',action='store_true',help='Rebuild and validate stored snapshots without claiming a fresh network check')
    args=parser.parse_args()
    run_group(args.group,args.output_dir,args.offline)
