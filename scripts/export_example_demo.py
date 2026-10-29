#!/usr/bin/env python3
"""Export the verified example as Newsshow-Demo repository media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def export(source, destination):
    source,destination=Path(source),Path(destination)
    manifest=json.loads((source/'example-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('fixture_id')!='newsshow-allgemein-de-v1' or manifest.get('is_example') is not True:
        raise ValueError('Only the prepared example may be exported as repository demo')
    video=source/'main/latest.mp4';preview=source/'main/preview.png'
    if hashlib.sha256(video.read_bytes()).hexdigest()!=manifest.get('sha256'):
        raise ValueError('Example checksum mismatch')
    if not preview.is_file():raise ValueError('Missing example preview')
    destination.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(video,destination/'newsshow-demo.mp4')
    shutil.copyfile(preview,destination/'newsshow-demo.png')
    metadata={'title':'Newsshow-Demo','publication_kind':'repository-demo',
        'video':'newsshow-demo.mp4','preview':'newsshow-demo.png','source':manifest}
    (destination/'newsshow-demo.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('out/example-show'))
    parser.add_argument('--destination',type=Path,default=Path('demos'))
    args=parser.parse_args();export(args.source,args.destination)
