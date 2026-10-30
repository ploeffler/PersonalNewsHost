#!/usr/bin/env python3
"""Render maintained Graphviz sources as PNG and SVG for docs and GitHub Wiki."""
import argparse
from pathlib import Path
try:
    from .check_documentation_release import validate_release
except ImportError:
    from check_documentation_release import validate_release
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DIAGRAMS=ROOT/'docs/guide/assets/workflows'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-tag',required=True)
    args=parser.parse_args()
    validate_release(args.release_tag)
    for source in sorted(DIAGRAMS.glob('*.dot')):
        for kind in ('svg','png'):
            subprocess.run(['dot',f'-T{kind}','-Gdpi=144',str(source),'-o',str(source.with_suffix('.'+kind))],check=True)
        print(source.stem)


if __name__=='__main__':main()
