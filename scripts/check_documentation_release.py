#!/usr/bin/env python3
"""Fail closed unless documentation targets a confirmed completed subversion."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def validate_release(tag,root=ROOT):
    if not isinstance(tag,str) or not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?',tag):
        raise ValueError('A version tag such as v0.1 is required')
    root=Path(root)
    marker=json.loads((root/'planning/documentation-release.json').read_text(encoding='utf-8'))
    if marker.get('completed') is not True or marker.get('tests_passed') is not True:
        raise ValueError('Subversion is not confirmed complete and tested')
    version=(root/'VERSION').read_text(encoding='utf-8').strip()
    if marker.get('version')!=version or tag!='v'+version:
        raise ValueError('Release marker, VERSION and tag must match')
    if marker.get('branch')!='Full-featured-Newsoutlet':
        raise ValueError('Documentation must originate from the development branch')
    board_path=root/'planning/task-board.json'
    if board_path.is_file():
        board=json.loads(board_path.read_text(encoding='utf-8'))
        release=next((item for item in board.get('releases',[]) if item['version']==version),None)
        tasks={task['id']:task for task in board.get('tasks',[])}
        if not release or any(ident not in tasks or tasks[ident]['status']!='done' or tasks[ident].get('local_work_pending') for ident in release['tasks']):
            raise ValueError('Subversion task board is not complete')
    return version


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag',required=True)
    args=parser.parse_args()
    try:version=validate_release(args.tag)
    except (ValueError,OSError) as exc:parser.exit(1,f'Documentation blocked: {exc}\n')
    print('Confirmed documentation release:',version)


if __name__=='__main__':main()
