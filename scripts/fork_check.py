#!/usr/bin/env python3
"""Compare every fork branch with upstream; optional managed GitHub issue notice."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
SHA = re.compile(r'^[0-9a-f]{40}$')
ISSUE_MARKER = '<!-- personalnewshost-fork-status -->'
ISSUE_LABEL = 'personalnewshost-fork-sync'


class APIError(RuntimeError):
    def __init__(self, code):
        self.code = str(code)
        super().__init__('GitHub operation failed: ' + self.code)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHub:
    def __init__(self, token=None):
        self.token = token if token is not None else os.environ.get('GITHUB_TOKEN', '')
        self.opener = build_opener(NoRedirect())
        self.blocked_until = 0

    def call(self, method, path, body=None):
        if time.time() < self.blocked_until:
            raise APIError('rate_limited')
        for attempt in range(3):
            try:
                return self._request(method, path, body)
            except APIError as error:
                if method != 'GET' or error.code not in ('network_or_response', '500', '502', '503', '504') or attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    def _request(self, method, path, body=None):
        if not path.startswith('/repos/'):
            raise APIError('invalid_path')
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'PersonalNewsHost-fork-sync'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = Request('https://api.github.com' + path, method=method, headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener.open(request, timeout=15) as response:
                data = response.read(4_000_001)
                if len(data) > 4_000_000:
                    raise APIError('response_limit')
                return json.loads(data) if data else {}
        except HTTPError as error:
            code = error.code
            headers = error.headers or {}
            if code == 429 or (code == 403 and headers.get('X-RateLimit-Remaining') == '0'):
                try:
                    delay = max(60, float(headers.get('Retry-After', 0)),
                                float(headers.get('X-RateLimit-Reset', time.time())) - time.time())
                except (ValueError, TypeError):
                    delay = 60
                self.blocked_until = time.time() + min(86400, delay)
            error.close()
            raise APIError(code) from None
        except (OSError, URLError, ValueError):
            # Never expose request headers, raw errors or authentication tokens.
            raise APIError('network_or_response') from None

    def pages(self, path):
        for page in range(1, 101):
            batch = self.call('GET', path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
            if not isinstance(batch, list):
                raise APIError('invalid_list')
            yield from batch
            if len(batch) < 100:
                return
        raise APIError('page_limit')


def repository(value):
    if not isinstance(value, str) or not REPO.fullmatch(value) or any(part in ('.', '..') for part in value.split('/')):
        raise APIError('invalid_repository')
    return value


def branch_path(repo, branch):
    return '/repos/' + repository(repo) + '/branches/' + quote(branch, safe='')


def branches(api, repo):
    result = {}
    for item in api.pages('/repos/' + repository(repo) + '/branches'):
        name, sha = item.get('name'), item.get('commit', {}).get('sha', '')
        if not isinstance(name, str) or not name or len(name) > 1024 or any(c in name for c in '\r\n\x00') or not SHA.fullmatch(sha):
            raise APIError('invalid_branch')
        result[name] = {'sha': sha, 'protected': bool(item.get('protected', False))}
    return result


def scan(api, fork, upstream=None):
    fork = repository(fork)
    info = api.call('GET', '/repos/' + fork)
    if not info.get('fork'):
        raise APIError('not_a_fork')
    related = {info.get(key, {}).get('full_name') for key in ('parent', 'source')}
    upstream = repository(upstream or info.get('source', {}).get('full_name') or info.get('parent', {}).get('full_name'))
    if upstream.lower() == fork.lower() or upstream not in related:
        raise APIError('upstream_not_parent_or_source')
    theirs, ours = branches(api, upstream), branches(api, fork)
    report = {'fork': fork, 'upstream': upstream, 'checked_at': time.time(), 'branches': [], 'error': None}
    owner = fork.split('/')[0]
    for name in sorted(set(ours) | set(theirs)):
        local, remote = ours.get(name), theirs.get(name)
        row = {'branch': name, 'fork_sha': local['sha'] if local else None,
               'upstream_sha': remote['sha'] if remote else None,
               'protected': local['protected'] if local else False,
               'ahead': None, 'behind': None, 'status': 'fork_only' if not remote else 'upstream_only'}
        if local and remote:
            row['compare_url'] = 'https://github.com/' + upstream + '/compare/' + remote['sha'] + '...' + owner + ':' + local['sha']
            if local['sha'] == remote['sha']:
                row.update(ahead=0, behind=0, status='current')
            else:
                try:
                    data = api.call('GET', '/repos/' + upstream + '/compare/' + remote['sha'] + '...' + owner + ':' + local['sha'])
                    ahead, behind = data['ahead_by'], data['behind_by']
                    if any(type(v) is not int or v < 0 for v in (ahead, behind)):
                        raise APIError('invalid_comparison')
                    row.update(ahead=ahead, behind=behind,
                               status='diverged' if ahead and behind else 'behind' if behind else 'ahead' if ahead else 'current')
                except (APIError, KeyError, TypeError) as error:
                    row.update(status='unknown', error=error.code if isinstance(error, APIError) else 'invalid_comparison')
        report['branches'].append(row)
    return report


def fingerprint(report):
    changed = [{key: row.get(key) for key in ('branch', 'fork_sha', 'upstream_sha', 'ahead', 'behind', 'status', 'error')}
               for row in report['branches'] if row.get('behind') or row['status'] == 'unknown']
    return hashlib.sha256(json.dumps([report['fork'], report['upstream'], changed], sort_keys=True).encode()).hexdigest()


def markdown(report):
    def escape(value):
        return html.escape(str(value)).replace('|', '\\|').replace('`', '\\`')
    lines = ['## Fork-/Upstream-Abgleich', '', f"Fork: {report['fork']} · Original: {report['upstream']}", '',
             '| Branch | Status | Ahead | Behind | Vergleich |', '|---|---|---:|---:|---|']
    for row in report['branches']:
        link = '[Vergleich](' + row['compare_url'] + ')' if row.get('compare_url') else '–'
        lines.append('| ' + ' | '.join(escape(row.get(key) if row.get(key) is not None else '–')
                                      for key in ('branch', 'status', 'ahead', 'behind')) + ' | ' + link + ' |')
    if report.get('synchronization'):
        lines += ['', '### Übernahmeergebnis', '', '| Branch | Ergebnis | Konflikt/Schutz |', '|---|---|---|']
        for result in report['synchronization']:
            link = '[Pull Request vorbereiten](' + result['pull_request_url'] + ')' if result.get('pull_request_url') else '–'
            lines.append('| ' + escape(result['branch']) + ' | ' + escape(result['result']) + ' | ' + link + ' |')
    lines += ['', 'Eigene Commits werden nicht überschrieben. `unknown` bedeutet Prüfungsfehler, nicht aktuell.',
              '[Synchronisierung starten](https://github.com/' + report['fork'] + '/actions/workflows/fork-sync.yml): Workflow manuell starten und Branch auswählen.',
              'Dieser Hinweis ist der Stand des letzten geänderten Rückstands; die aktuelle Gesamtliste steht in der Actions-Zusammenfassung.']
    return '\n'.join(lines) + '\n'


def notify(api, report):
    digest = '<!-- fork-state:' + fingerprint(report) + ' -->'
    issue = next((item for item in api.pages('/repos/' + report['fork'] + '/issues?state=all&labels=' + ISSUE_LABEL)
                  if not item.get('pull_request') and any(label.get('name') == ISSUE_LABEL for label in item.get('labels', [])) and ISSUE_MARKER in (item.get('body') or '')), None)
    active = any(row.get('behind') or row['status'] == 'unknown' for row in report['branches'])
    body = ISSUE_MARKER + '\n' + digest + '\n' + markdown(report)
    if issue and digest in (issue.get('body') or ''):
        return 'unchanged'
    if not issue:
        if not active:
            return 'no_backlog'
        try:
            api.call('GET', '/repos/' + report['fork'] + '/labels/' + ISSUE_LABEL)
        except APIError as error:
            if error.code != '404':
                raise
            api.call('POST', '/repos/' + report['fork'] + '/labels', {'name': ISSUE_LABEL, 'color': '0969da'})
        api.call('POST', '/repos/' + report['fork'] + '/issues',
                 {'title': 'Fork: Änderungen im Originalrepository verfügbar', 'body': body, 'labels': [ISSUE_LABEL]})
        return 'created'
    path = '/repos/' + report['fork'] + '/issues/' + str(issue['number'])
    api.call('PATCH', path, {'body': body, 'state': 'open' if active else 'closed'})
    api.call('POST', path + '/comments', {'body': markdown(report)})
    return 'updated'


def output(report, path=None):
    if path:
        try:
            from .update_check import save
        except ImportError:
            from update_check import save
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        save(path, report)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as stream:
            stream.write(markdown(report))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fork', required=True, help='OWNER/REPO')
    parser.add_argument('--upstream', help='Defaults to the verified fork parent')
    parser.add_argument('--notify', action='store_true', help='Create/update managed issue in fork')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        api = GitHub()
        report = scan(api, args.fork, args.upstream)
        output(report, args.report)
        if args.notify:
            report['notification'] = notify(api, report)
        print(json.dumps(report, ensure_ascii=False))
        return 1 if any(row['status'] == 'unknown' for row in report['branches']) else 0
    except (APIError, OSError, ValueError) as error:
        print('Fork check failed: ' + (error.code if isinstance(error, APIError) else 'local_or_response_error'), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
