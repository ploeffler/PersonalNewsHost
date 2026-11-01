#!/usr/bin/env python3
"""Explicit, non-forcing remote fork synchronization; never changes local files."""
import argparse
import json
import os
from urllib.parse import quote

try:
    from .fork_check import APIError, GitHub, branch_path, scan, notify, output
except ImportError:
    from fork_check import APIError, GitHub, branch_path, scan, notify, output


def synchronize(api, report, selected=(), all_behind=False, merge=False):
    if all_behind and (selected or merge):
        raise ValueError('Automatic batch only supports fast-forward branches')
    if not all_behind and not selected:
        raise ValueError('Select branches explicitly')
    rows = {row['branch']: row for row in report['branches'] if row.get('fork_sha')}
    names = sorted(name for name, row in rows.items() if row['status'] == 'behind') if all_behind else sorted(set(selected))
    results = []
    for name in names:
        row = rows.get(name)
        result = {'branch': name, 'result': 'not_eligible'}
        if row and row['status'] in ('current', 'ahead'):
            result['result'] = 'already_' + row['status']
        if row and row['status'] in ('behind', 'diverged'):
            result['pull_request_url'] = ('https://github.com/' + report['fork'] + '/compare/' + quote(name, safe='')
                                          + '...' + report['upstream'].split('/')[0] + ':' + quote(row.get('upstream_branch', name), safe='') + '?expand=1')
            if row['protected']:
                result['result'] = 'protected_use_pull_request'
            elif row['status'] == 'diverged' and not merge:
                result['result'] = 'diverged_requires_explicit_merge'
            else:
                try:
                    ours_data = api.call('GET', branch_path(report['fork'], name))
                    ours = ours_data['commit']['sha']
                    theirs = api.call('GET', branch_path(report['upstream'], row.get('upstream_branch', name)))['commit']['sha']
                    if ours_data.get('protected'):
                        result['result'] = 'protected_use_pull_request'
                    elif ours != row['fork_sha'] or theirs != row['upstream_sha']:
                        result['result'] = 'heads_changed_retry_check'
                    elif row['status'] == 'behind':
                        api.call('PATCH', '/repos/' + report['fork'] + '/git/refs/heads/' + quote(name, safe=''),
                                 {'sha': theirs, 'force': False})
                        result['result'] = 'fast_forwarded'
                    else:
                        api.call('POST', '/repos/' + report['fork'] + '/merges', {'base': name, 'head': theirs})
                        result['result'] = 'merged_preserving_own_commits'
                except APIError as error:
                    result['result'] = 'merge_conflict' if error.code == '409' else 'blocked_or_unknown'
                    result['error'] = error.code
                except (KeyError, TypeError):
                    result['result'] = 'invalid_head_response'
        results.append(result)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fork', required=True)
    parser.add_argument('--upstream')
    parser.add_argument('--branch-map-json', default=os.environ.get('FORK_SYNC_BRANCH_MAP') or '{}')
    parser.add_argument('--branch', action='append', default=[])
    parser.add_argument('--all-behind', action='store_true')
    parser.add_argument('--merge', action='store_true', help='Allow preserving merge of explicitly selected divergent branch')
    parser.add_argument('--notify', action='store_true')
    parser.add_argument('--report')
    args = parser.parse_args(argv)
    try:
        api = GitHub()
        mapping = json.loads(args.branch_map_json)
        report = scan(api, args.fork, args.upstream, mapping)
        results = synchronize(api, report, args.branch, args.all_behind, args.merge)
        # Refresh rather than reporting a timed-out or protected write as success.
        fresh = scan(api, args.fork, report['upstream'], mapping)
        fresh['synchronization'] = results
        output(fresh, args.report)
        if args.notify:
            fresh['notification'] = notify(api, fresh)
        print(json.dumps(fresh, ensure_ascii=False))
        return 1 if any(r['result'] not in ('fast_forwarded', 'merged_preserving_own_commits', 'already_current', 'already_ahead') for r in results) or any(row['status'] == 'unknown' for row in fresh['branches']) else 0
    except (APIError, OSError, ValueError) as error:
        print('Fork synchronization failed: ' + (error.code if isinstance(error, APIError) else 'local_or_selection_error'))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
