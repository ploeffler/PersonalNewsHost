#!/usr/bin/env python3
"""Combine successful research groups and refresh the shared favicon cache once."""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
try:
    from .run import GROUPS
    from .validate_catalogs import ROOT,validate
    from .collect_source_logos import refresh_logos,DEFAULT_ASSETS
except ImportError:
    from run import GROUPS
    from validate_catalogs import ROOT,validate
    from collect_source_logos import refresh_logos,DEFAULT_ASSETS


def package(input_dir,output_dir,cache_dir=DEFAULT_ASSETS,refresh_days=30):
    input_dir,output_dir=Path(input_dir),Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=False)
    manifest={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'groups':{}}
    def save():
        (output_dir/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    save()
    try:
        for folder in sorted(input_dir.iterdir()):
            if not folder.is_dir() or not (folder/'manifest.json').is_file():continue
            source=json.loads((folder/'manifest.json').read_text())
            group=source.get('group')
            if group not in GROUPS or source.get('status')!='success':continue
            if group in manifest['groups']:raise ValueError('Duplicate research group: '+group)
            checked=validate(group,folder)
            for relative in GROUPS[group]['files']:
                target=output_dir/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(folder/relative,target)
            report=output_dir/'research-runs'/group
            report.mkdir(parents=True)
            shutil.copyfile(folder/'manifest.json',report/'manifest.json')
            if (folder/'run.log').is_file():shutil.copyfile(folder/'run.log',report/'run.log')
            manifest['groups'][group]={'validation':checked,'mode':source.get('mode','unknown')}
        if not manifest['groups']:raise ValueError('No successful research groups to package')
        manifest['logos']=refresh_logos(catalog_root=output_dir,output_dir=output_dir/'docs/assets/source-logos',cache_dir=cache_dir,groups=tuple(manifest['groups']),refresh_days=refresh_days)
        manifest['status']='success'
    except Exception as error:
        manifest['status']='failed';manifest['error']=f'{type(error).__name__}: {error}'
        raise
    finally:
        manifest['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds');save()
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--cache-dir',type=Path,default=DEFAULT_ASSETS)
    parser.add_argument('--refresh-days',type=int,default=30)
    args=parser.parse_args()
    print(json.dumps(package(args.input_dir,args.output_dir,args.cache_dir,args.refresh_days),ensure_ascii=False))
