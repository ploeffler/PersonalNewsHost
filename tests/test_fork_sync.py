"""T196: no-force writes, preserving merges, branch races and protected refs."""
import copy
import unittest
from scripts.fork_check import APIError
from scripts.fork_sync import synchronize

A, B, C = 'a' * 40, 'b' * 40, 'c' * 40


class SyncAPI:
    def __init__(self):
        self.writes = []
        self.gets = []
        self.fork_sha, self.upstream_sha = A, B
        self.protected = False
        self.fail = None
    def call(self, method, path, body=None):
        if method == 'GET':
            self.gets.append(path)
            return {'commit': {'sha': self.fork_sha if '/user/' in path else self.upstream_sha}, 'protected': self.protected}
        self.writes.append((method, path, body))
        if self.fail:raise APIError(self.fail)
        self.fork_sha = B if method == 'PATCH' else C
        return {}


def report(status='behind', protected=False):
    return {'fork': 'user/project', 'upstream': 'original/project', 'branches': [
        {'branch': 'feature/topic', 'status': status, 'fork_sha': A, 'upstream_sha': B,
         'protected': protected, 'ahead': 2 if status == 'diverged' else 0, 'behind': 3}]}


class ForkSyncTests(unittest.TestCase):
    def test_fast_forward_is_explicit_and_never_forced(self):
        api = SyncAPI()
        self.assertEqual(synchronize(api, report(), ['feature/topic'])[0]['result'], 'fast_forwarded')
        self.assertEqual(api.writes[0], ('PATCH', '/repos/user/project/git/refs/heads/feature%2Ftopic', {'sha': B, 'force': False}))

    def test_mapped_work_branch_rechecks_right_upstream_and_retains_its_name(self):
        api = SyncAPI();data = report();data['branches'][0]['upstream_branch'] = 'original/topic'
        result = synchronize(api, data, ['feature/topic'])[0]
        self.assertIn('/repos/original/project/branches/original%2Ftopic', api.gets)
        self.assertEqual(api.writes[0][1], '/repos/user/project/git/refs/heads/feature%2Ftopic')
        self.assertIn('original%2Ftopic', result['pull_request_url'])

    def test_divergence_requires_explicit_merge_and_preserves_own_history(self):
        api = SyncAPI()
        self.assertEqual(synchronize(api, report('diverged'), ['feature/topic'])[0]['result'], 'diverged_requires_explicit_merge')
        self.assertEqual(api.writes, [])
        self.assertEqual(synchronize(api, report('diverged'), ['feature/topic'], merge=True)[0]['result'], 'merged_preserving_own_commits')
        self.assertEqual(api.writes[0], ('POST', '/repos/user/project/merges', {'base': 'feature/topic', 'head': B}))

    def test_batch_only_updates_behind_not_diverged_or_fork_only(self):
        api = SyncAPI();data = report()
        for status in ['current', 'ahead', 'diverged', 'fork_only', 'upstream_only', 'unknown']:
            row = copy.deepcopy(data['branches'][0]);row.update(branch=status, status=status);data['branches'].append(row)
        results = synchronize(api, data, all_behind=True)
        self.assertEqual([r['branch'] for r in results], ['feature/topic'])
        self.assertEqual(len(api.writes), 1)

    def test_heads_changed_blocks_write(self):
        for side in ['fork_sha', 'upstream_sha']:
            api = SyncAPI();setattr(api, side, C)
            self.assertEqual(synchronize(api, report(), ['feature/topic'])[0]['result'], 'heads_changed_retry_check')
            self.assertEqual(api.writes, [])

    def test_protection_snapshot_and_recheck_both_block_write(self):
        api = SyncAPI()
        self.assertEqual(synchronize(api, report(protected=True), ['feature/topic'])[0]['result'], 'protected_use_pull_request')
        api.protected = True
        self.assertEqual(synchronize(api, report(), ['feature/topic'])[0]['result'], 'protected_use_pull_request')
        self.assertEqual(api.writes, [])

    def test_conflict_permission_and_ambiguous_failure_do_not_blindly_retry(self):
        for code, expected in [('409', 'merge_conflict'), ('403', 'blocked_or_unknown'), ('network_or_response', 'blocked_or_unknown')]:
            api = SyncAPI();api.fail = code
            result = synchronize(api, report('diverged'), ['feature/topic'], merge=True)
            self.assertEqual(result[0]['result'], expected)
            self.assertEqual(len(api.writes), 1)

    def test_already_current_is_idempotent_and_selection_is_required(self):
        api = SyncAPI()
        self.assertEqual(synchronize(api, report('current'), ['feature/topic'])[0]['result'], 'already_current')
        self.assertEqual(api.writes, [])
        with self.assertRaises(ValueError):synchronize(api, report())
        with self.assertRaises(ValueError):synchronize(api, report(), all_behind=True, merge=True)
