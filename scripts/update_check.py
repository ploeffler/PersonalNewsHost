#!/usr/bin/env python3
"""Read-only upstream checks. Never fetch code into the installation or install it."""
import argparse
import base64
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ploeffler/PersonalNewsHost'
API = 'https://api.github.com/repos/' + REPOSITORY
RAW = 'https://raw.githubusercontent.com/' + REPOSITORY
VERSION = re.compile(r'^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*))?(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$')
SHA = re.compile(r'^[0-9a-f]{40}$')


class CheckError(ValueError):
    pass


def version_key(value):
    match = VERSION.fullmatch(value)
    if not match:
        raise CheckError('invalid_version')
    major, minor, patch, pre = match.groups()
    identifiers = []
    if pre:
        for ident in pre.split('.'):
            if not ident or (ident.isdigit() and len(ident) > 1 and ident[0] == '0'):
                raise CheckError('invalid_version')
            identifiers.append((0, int(ident)) if ident.isdigit() else (1, ident))
    return int(major), int(minor), int(patch or 0), not bool(pre), tuple(identifiers)


def fetch_json(url):
    # Only public origin metadata is requested. No GitHub login, configuration,
    # environment token or provider secret is consulted.
    request = Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'PersonalNewsHost-update-check'})
    with urlopen(request, timeout=10) as response:
        if response.geturl() != url:
            raise CheckError('unexpected_redirect')
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise CheckError('response_too_large')
        return json.loads(data)


def installed(root):
    root = Path(root)
    version = (root / 'VERSION').read_text().strip()
    version_key(version)
    build = root / 'build-info.json'
    if build.exists():
        info = json.loads(build.read_text())
        if info.get('version') != version or not SHA.fullmatch(info.get('commit', '')):
            raise CheckError('invalid_build_identity')
        digest = info.get('image_digest')
        if digest is not None and not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise CheckError('invalid_build_identity')
        tag = info.get('tag')
        if tag is not None and version_key(tag) != version_key(version):
            raise CheckError('invalid_build_identity')
        return dict(version=version, commit=info['commit'], tag=tag, local_changes=False,
                    image_digest=digest, identity_source='build-info.json')
    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    try:
        top = git('rev-parse', '--show-toplevel')
        commit = git('rev-parse', 'HEAD') if top and Path(top).resolve() == root.resolve() else None
        tag = git('describe', '--tags', '--exact-match', 'HEAD') if commit else None
        dirty = bool(git('status', '--porcelain')) if commit else False
    except (OSError, subprocess.SubprocessError):
        commit, tag, dirty = None, None, False
    if tag and (not VERSION.fullmatch(tag) or version_key(tag) != version_key(version)):
        tag = None
    return {'version': version, 'commit': commit if commit and SHA.fullmatch(commit) else None,
            'tag': tag, 'local_changes': dirty, 'image_digest': None,
            'identity_source': 'checkout' if commit else 'VERSION_only'}


def catalog(get=fetch_json, channel='stable'):
    candidates = []
    for page in range(1, 6):
        batch = get(API + f'/tags?per_page=100&page={page}')
        if not isinstance(batch, list):
            raise CheckError('invalid_catalog')
        for item in batch:
            tag, commit = item.get('name', ''), item.get('commit', {}).get('sha', '')
            try:
                key = version_key(tag)
            except CheckError:
                continue
            if not tag.startswith('v') or not SHA.fullmatch(commit):
                continue
            if channel == 'stable' and not key[3]:
                continue
            candidates.append((key, tag, commit))
        if len(batch) < 100:
            return sorted(candidates, reverse=True)
    raise CheckError('catalog_page_limit')


def select_release(current, seen, get=fetch_json, channel='stable'):
    candidates = catalog(get, channel)
    observed = dict(seen)
    for _, tag, commit in candidates:
        if (tag in seen and seen[tag] != commit) or (current['tag'] == tag and current['commit'] and current['commit'] != commit):
            raise CheckError('tag_changed')
        observed[tag] = commit
    # Reject ambiguous/truncated discovery rather than silently declaring current.
    for _, tag, commit in candidates[:20]:
        try:
            marker = get(RAW + '/' + commit + '/planning/documentation-release.json')
        except HTTPError as error:
            if error.code == 404:
                error.close()
                continue
            raise
        if not isinstance(marker, dict) or marker.get('version') != tag[1:] or marker.get('completed') is not True or marker.get('tests_passed') is not True or marker.get('branch') != 'Full-featured-Newsoutlet':
            continue
        metadata = get(API + '/contents/VERSION?ref=' + commit)
        if metadata.get('encoding') != 'base64' or base64.b64decode(metadata['content']).decode().strip() != marker['version']:
            raise CheckError('release_version_mismatch')
        try:
            release = get(API + '/releases/tags/' + tag)
        except HTTPError as error:
            if error.code != 404:
                raise
            # This project publishes confirmed version tags without requiring
            # a separate GitHub Release object (e.g. its original v0.1).
            error.close()
            release = {}
        if release.get('draft') or (channel == 'stable' and release.get('prerelease')):
            continue
        latest = {'tag': tag, 'commit': commit,
                  'notes_url': 'https://github.com/' + REPOSITORY + '/releases/tag/' + tag,
                  'notes': str(release.get('body') or 'Confirmed version tag; no separate release notes supplied.')[:6000],
                  'compatibility': 'requires_installation_preflight'}
        return latest, observed
    if len(candidates) > 20:
        raise CheckError('release_candidate_limit')
    return None, observed


def save(path, value):
    descriptor, name = tempfile.mkstemp(prefix='.update-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def check(root=ROOT, state=None, interval=86400, force=False, channel='stable', get=fetch_json, now=None):
    if channel not in ('stable', 'development') or type(interval) is not int or not 60 <= interval <= 604800:
        raise CheckError('invalid_settings')
    now = time.time() if now is None else now
    folder = Path(state) if state else Path(root) / 'state' / 'updates'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'check.json'
    descriptor = os.open(folder / 'check.lock', os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(old, dict):
            raise CheckError('invalid_state')
        result = dict(old, repository=REPOSITORY, channel=channel, last_attempt_at=now,
                      update_available=False, error=None)
        try:
            current = installed(root)
            if not force and old.get('channel') == channel and old.get('installed') == current and old.get('next_check_at', 0) > now:
                return old
            latest, seen = select_release(current, old.get('seen_tags', {}), get, channel)
            available = bool(latest and version_key(latest['tag']) > version_key(current['version']))
            result.update(installed=current, latest_release=latest, seen_tags=seen,
                          update_available=available, last_success_at=now, failures=0,
                          status='update_available' if available else 'current_or_development', next_check_at=now + interval)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
            failures = min(int(old.get('failures', 0)) + 1, 10)
            reason = str(error) if isinstance(error, CheckError) else 'check_failed'
            retry_after = 0
            if isinstance(error, HTTPError) and error.code in (403, 429):
                reason = 'rate_limited'
                try:
                    retry_after = max(float(error.headers.get('Retry-After', 0)),
                                      float(error.headers.get('X-RateLimit-Reset', now)) - now)
                except (TypeError, ValueError):
                    retry_after = 0
            if isinstance(error, HTTPError):
                error.close()
            result.update(status='check_failed', error=reason, failures=failures,
                          next_check_at=now + min(86400, max(60, retry_after, 60 * 2 ** failures)))
            # Previous successful metadata remains visible but is not actionable.
        save(path, result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path)
    parser.add_argument('--interval', type=int, default=86400)
    parser.add_argument('--channel', choices=['stable', 'development'], default='stable')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args(argv)
    last_attempt = None
    try:
        while True:
            result = check(state=args.state, interval=args.interval, channel=args.channel, force=args.force)
            if result.get('last_attempt_at') != last_attempt:
                print(json.dumps(result, ensure_ascii=False), flush=True)
                last_attempt = result.get('last_attempt_at')
            args.force = False
            if not args.watch:
                return 1 if result.get('error') else 0
            time.sleep(min(60, max(1, result['next_check_at'] - time.time())))
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError):
        print('Update check failed; inspect private state and permissions (values redacted).', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
