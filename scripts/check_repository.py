#!/usr/bin/env python3
"""Local CI: syntax, secrets, document links and tests with network denied."""
import ast
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path
import re
import socket
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def tracked():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    return [ROOT/name for name in names if name and (ROOT/name).is_file()]


def secrets(paths):
    patterns=[re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:proj-|svcacct-|ant-)[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{48})\b'),
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


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ('id', 'name'):
            if attrs.get(name): self.anchors.add(attrs[name])
        for name in ('href', 'src', 'poster'):
            if attrs.get(name): self.targets.append(attrs[name])


def site_links(root):
    """Validate generated HTML local assets and fragment links without HTTP."""
    root = Path(root).resolve()
    pages = {}
    for path in root.rglob('*.html'):
        parser = PageLinks()
        parser.feed(path.read_text(encoding='utf-8'))
        pages[path.resolve()] = parser
    errors = []
    for path, parser in pages.items():
        for target in parser.targets:
            url = urlsplit(target)
            if url.scheme or url.netloc: continue
            target_path = unquote(url.path)
            destination = ((root / target_path.lstrip('/')) if target_path.startswith('/')
                           else path.parent / target_path).resolve() if target_path else path
            if destination.is_dir(): destination = destination / 'index.html'
            if not destination.is_relative_to(root) or not destination.is_file():
                errors.append(f'{path.relative_to(root)}: missing or escaping local target {target}')
            elif url.fragment and destination in pages and unquote(url.fragment) not in pages[destination].anchors:
                errors.append(f'{path.relative_to(root)}: missing anchor {target}')
    return errors


@contextmanager
def offline_network():
    # Reversible Python guard for local runs. CI additionally uses a network
    # namespace so subprocesses (including FFmpeg) cannot access the network.
    with patch.object(socket.socket, 'connect', no_network), \
         patch.object(socket.socket, 'connect_ex', no_network), \
         patch.object(socket.socket, 'sendto', no_network), \
         patch.object(socket, 'create_connection', no_network), \
         patch.object(socket, 'getaddrinfo', no_network):
        yield


def main():
    sys.path.insert(0,str(ROOT))
    paths=tracked()
    for path in paths:
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
    from scripts.security_checks import pinning_errors, scan_files, environment_secrets
    errors=secrets(paths)+links(paths)+pinning_errors()
    errors+=scan_files((ROOT/"docs").rglob("*"), values=environment_secrets(), publication=True)
    for error in errors:print(error,file=sys.stderr)
    if errors:return 1
    print('Syntax, secret scan and local Markdown links: OK',flush=True)
    with offline_network():
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
