#!/usr/bin/env python3
"""Fail-closed checks for textual secrets, publication paths and CI pinning.

Reports locations/categories only, never the matching secret or environment value.
Public news content is intentional; this is not an automatic personal-data classifier.
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import shlex
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:proj-|svcacct-|ant-)[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{48})\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'https?://[^\s/<>"\']+:[^\s/<>"\']+@', re.I),
    re.compile(r'[?&](?:access_token|api_key|token|password|secret)=[^\s&<>"\']+', re.I),
    re.compile(r'["\'](?:password|api_key|access_token|bot_token|chat_id)["\']\s*:\s*["\'][^"\']+["\']', re.I),
]
TRACKERS = re.compile(r'(?:google-analytics\.com|googletagmanager\.com|connect\.facebook\.net|analytics\.tiktok\.com)', re.I)


def environment_secrets(environ=None):
    environ = os.environ if environ is None else environ
    values = []
    for name, value in environ.items():
        if re.search(r'(?:TOKEN|PASSWORD|SECRET|CHAT_ID)(?:$|_)', name, re.I) and 8 <= len(value) <= 4096:
            values.append(value)
    return values


def public_source_url(value):
    parsed = urlsplit(str(value).strip())
    host = parsed.hostname or ''
    if ':' in host: host = '[' + host + ']'
    if parsed.port is not None: host += ':' + str(parsed.port)
    return urlunsplit((parsed.scheme, host, parsed.path, '', ''))


def configuration_secrets(config):
    values = []
    def visit(value, key=''):
        if isinstance(value, dict):
            for name, child in value.items(): visit(child, str(name))
        elif isinstance(value, list):
            for child in value: visit(child, key)
        elif isinstance(value, str):
            if re.search(r'(?:token|password|api_key|chat_id|contact_email|owner_email|private_email)', key, re.I) and value:
                values.append(value)
            # Preserve the raw URL as a known secret to block publication too.
            if re.search(r'https?://[^/]+@|[?&](?:token|api_key|access_token|password|secret)=', value, re.I):
                values.append(value)
    visit(config)
    return values


def scan_files(paths, *, root=ROOT, values=(), publication=False):
    root = Path(root).resolve()
    errors = []
    for path in sorted(set(Path(p) for p in paths)):
        resolved = path.resolve()
        try:
            relative = path.absolute().relative_to(root)
            resolved.relative_to(root)
        except ValueError:
            errors.append('output escapes repository boundary')
            continue
        label = str(relative)
        if '.git' in relative.parts:
            errors.append(label + ': Git metadata must not be published')
            continue
        if publication and (path.name.startswith('.env') or path.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.pem', '.key'} or 'state' in relative.parts):
            errors.append(label + ': private state/configuration must not be published')
            continue
        if not path.is_file():
            continue
        # Streaming, including large artifacts. Overlap detects boundary-spanning
        # tokens; UTF-8 news text remains untouched and is never logged.
        tail = ''
        with path.open('rb') as source:
            while chunk := source.read(65536):
                text = tail + chunk.decode('utf-8', errors='ignore')
                if any(pattern.search(text) for pattern in PATTERNS) or any(v in text for v in values):
                    errors.append(label + ': secret-like content detected')
                    break
                if publication and path.suffix.lower() in {'.html', '.js'} and TRACKERS.search(text):
                    errors.append(label + ': third-party tracker detected')
                    break
                tail = text[-8192:]
    return errors


def pinning_errors(root=ROOT):
    root = Path(root)
    errors = []
    pins = {}
    for filename in ('requirements.txt', 'requirements-constraints.txt'):
        for line in (root / filename).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)', line)
            if not match:
                errors.append(filename + ': dependency is not pinned exactly')
            else:
                pins[re.sub(r'[-_.]+', '-', match[1]).lower()] = match[2]
    for path in sorted((root / '.github/workflows').glob('*.yml')):
        text = path.read_text()
        for action in re.findall(r'\buses:\s*([^\s#]+)', text):
            if not action.startswith('./') and not re.fullmatch(r'[^@]+@[0-9a-f]{40}', action):
                errors.append(path.name + ': Action is not pinned to a commit')
        for line in text.splitlines():
            if 'pip install' not in line:
                continue
            if 'PIP_CONSTRAINT: ${{ github.workspace }}/requirements-constraints.txt' not in text:
                errors.append(path.name + ': missing global pip constraint')
            command = line.split('pip install', 1)[1]
            args = shlex.split(command)
            skip = False
            for arg in args:
                if skip:
                    skip = False
                    continue
                if arg in {'-r', '-c', '--requirement', '--constraint', '--index-url', '--extra-index-url', '--find-links'}:
                    skip = True
                    continue
                if arg.startswith('-'):
                    continue
                name = re.split(r'[<>=!~\[]', arg)[0]
                if re.sub(r'[-_.]+', '-', name).lower() not in pins:
                    errors.append(path.name + ': direct pip dependency missing exact constraint')
        for package in re.findall(r'\bnpm install[^\n]*', text):
            for arg in shlex.split(package)[2:]:
                if not arg.startswith('-') and not re.fullmatch(r'(?:@[^/]+/)?[^@]+@\d+\.\d+\.\d+(?:-[\w.-]+)?', arg):
                    errors.append(path.name + ': npm dependency is not pinned exactly')
    return errors


def output_files(patterns, root=ROOT):
    root = Path(root).resolve()
    paths = []
    for pattern in patterns:
        if not pattern.strip() or pattern.startswith('!'):
            continue  # Scan the superset of upload paths, including excluded files.
        for name in glob.glob(str(root / pattern.strip()), recursive=True, include_hidden=True):
            path = Path(name)
            paths.extend(path.rglob('*') if path.is_dir() else [path])
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outputs', nargs='+', default=[])
    parser.add_argument('--outputs-env')
    parser.add_argument('--pinning', action='store_true')
    parser.add_argument('--mask-config', type=Path)
    args = parser.parse_args()
    if args.mask_config:
        for value in configuration_secrets(json.loads(args.mask_config.read_text())):
            escaped = value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print('::add-mask::' + escaped)
        return 0
    patterns = args.outputs + (os.environ.get(args.outputs_env, '').splitlines() if args.outputs_env else [])
    errors = pinning_errors() if args.pinning else []
    if patterns:
        values = environment_secrets()
        config_path = ROOT / 'config.json'
        if config_path.is_file(): values += configuration_secrets(json.loads(config_path.read_text()))
        errors += scan_files(output_files(patterns), values=values, publication=True)
    if not patterns and not args.pinning:
        parser.error('Choose --pinning or output paths')
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print('Security checks: OK (no matching secrets, private state or configured trackers)')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
