#!/usr/bin/env python3
"""Local CI: syntax, secrets, document links and tests with network denied."""
import ast
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import unittest
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]


def tracked():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    return [ROOT/name for name in names if name and (ROOT/name).is_file()]


def secrets(paths):
    patterns=[re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:ant-)?[A-Za-z0-9_-]{20,})\b'),
              re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    errors=[]
    for path in paths:
        if path.stat().st_size>2_000_000:continue
        try:text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        for n,line in enumerate(text.splitlines(),1):
            if any(pattern.search(line) for pattern in patterns):errors.append(f'{path.relative_to(ROOT)}:{n}: secret-like content')
    return errors


def links(paths):
    errors=[]
    for path in paths:
        if path.suffix!='.md':continue
        # Only actual Markdown links, not raw strings in examples or YAML.
        for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)',path.read_text()):
            target=target.split('#',1)[0].split('?',1)[0].strip('<>')
            if not target or re.match(r'[a-zA-Z][\w+.-]*:',target) or target.startswith('/'):continue
            if not (path.parent/unquote(target)).exists():errors.append(f'{path.relative_to(ROOT)}: missing local link {target}')
    return errors


def no_network(*args,**kwargs):
    raise OSError('Network disabled by offline test runner')


def main():
    sys.path.insert(0,str(ROOT))
    paths=tracked()
    for path in paths:
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
    errors=secrets(paths)+links(paths)
    for error in errors:print(error,file=sys.stderr)
    if errors:return 1
    print('Syntax, secret scan and local Markdown links: OK',flush=True)
    socket.socket.connect=no_network
    socket.socket.connect_ex=no_network
    socket.create_connection=no_network
    socket.getaddrinfo=no_network
    socket.socket.sendto=no_network
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
