"""T195: full branch coverage, correct graph orientation and deduplicated notices."""
import copy
import unittest
from scripts.fork_check import APIError, GitHub, NoRedirect, scan, notify, markdown

FORK, UPSTREAM = 'user/project', 'original/project'
A, B = 'a' * 40, 'b' * 40


class FakeAPI:
    def __init__(self):
        self.ours = {'main': A, 'feature/topic': B, 'my-only': A}
        self.theirs = {'main': A, 'feature/topic': A, 'new-upstream': A}
        self.comparison = {'ahead_by': 0, 'behind_by': 3}
        self.issues = []
        self.writes = []
        self.gets = []

    def pages(self, path):
        if '/issues?' in path:return iter(copy.deepcopy(self.issues))
        data = self.ours if '/user/' in path else self.theirs
        return iter({'name': key, 'commit': {'sha': value}, 'protected': False} for key, value in data.items())

    def call(self, method, path, body=None):
        if method != 'GET':
            self.writes.append((method, path, body))
            if method == 'POST' and path.endswith('/issues'):
                self.issues = [{'number': 1, 'body': body['body'], 'labels': [{'name': value} for value in body.get('labels', [])]}]
            elif method == 'PATCH' and '/issues/' in path:
                self.issues[0].update(body)
            return {}
        self.gets.append(path)
        if '/compare/' in path:return copy.deepcopy(self.comparison)
        return {'fork': True, 'parent': {'full_name': UPSTREAM}, 'source': {'full_name': UPSTREAM}}


class ForkCheckTests(unittest.TestCase):
    def test_every_branch_including_nondefault_slash_and_missing_counterparts(self):
        api = FakeAPI();report = scan(api, FORK)
        rows = {row['branch']: row for row in report['branches']}
        self.assertEqual(set(rows), set(api.ours) | set(api.theirs))
        self.assertEqual(rows['main']['status'], 'current')
        self.assertEqual(rows['feature/topic']['behind'], 3)
        self.assertEqual(rows['my-only']['status'], 'fork_only')
        self.assertEqual(rows['new-upstream']['status'], 'upstream_only')
        self.assertIn('/compare/' + A + '...user:' + B, api.gets[-1])
        self.assertEqual(api.writes, [])

    def test_ahead_diverged_unknown_and_no_false_current(self):
        api = FakeAPI()
        for ahead, behind, status in [(2, 0, 'ahead'), (2, 3, 'diverged'), (0, 0, 'current')]:
            api.comparison = {'ahead_by': ahead, 'behind_by': behind}
            self.assertEqual(next(r for r in scan(api, FORK)['branches'] if r['branch'] == 'feature/topic')['status'], status)
        api.comparison = {'ahead_by': -1, 'behind_by': 0}
        self.assertEqual(next(r for r in scan(api, FORK)['branches'] if r['branch'] == 'feature/topic')['status'], 'unknown')

    def test_notice_only_on_new_or_changed_backlog_and_resolution(self):
        api = FakeAPI();report = scan(api, FORK)
        self.assertEqual(notify(api, report), 'created')
        count = len(api.writes)
        self.assertEqual(notify(api, report), 'unchanged')
        self.assertEqual(len(api.writes), count)
        api.comparison['behind_by'] = 4
        self.assertEqual(notify(api, scan(api, FORK)), 'updated')
        self.assertEqual(api.writes[-1][0], 'POST')
        api.ours['feature/topic'] = A
        self.assertEqual(notify(api, scan(api, FORK)), 'updated')
        self.assertEqual(api.issues[0]['state'], 'closed')

    def test_unlabelled_issue_cannot_spoof_managed_notice(self):
        from scripts.fork_check import ISSUE_MARKER, fingerprint
        api = FakeAPI();report = scan(api, FORK)
        api.issues = [{'number': 99, 'body': ISSUE_MARKER + '<!-- fork-state:' + fingerprint(report) + ' -->'}]
        self.assertEqual(notify(api, report), 'created')

    def test_current_fork_does_not_create_issue(self):
        api = FakeAPI();api.ours['feature/topic'] = A
        self.assertEqual(notify(api, scan(api, FORK)), 'no_backlog')
        self.assertEqual(api.writes, [])

    def test_pagination_fetches_more_than_first_hundred(self):
        class Pages(GitHub):
            def __init__(self):self.urls = []
            def call(self, method, path, body=None):
                self.urls.append(path)
                return list(range(100)) if path.endswith('&page=1') else ['last']
        api = Pages()
        self.assertEqual(len(list(api.pages('/repos/user/project/branches'))), 101)
        self.assertTrue(api.urls[-1].endswith('page=2'))

    def test_fork_of_fork_defaults_to_original_source_not_intermediate_parent(self):
        api = FakeAPI();original = api.call
        def call(method, path, body=None):
            if path == '/repos/' + FORK:
                return {'fork': True, 'parent': {'full_name': 'intermediate/project'}, 'source': {'full_name': UPSTREAM}}
            return original(method, path, body)
        api.call = call
        self.assertEqual(scan(api, FORK)['upstream'], UPSTREAM)

    def test_wrong_upstream_and_nonfork_rejected_before_any_write(self):
        api = FakeAPI()
        with self.assertRaises(APIError):scan(api, FORK, 'unrelated/project')
        api.call = lambda *args: {'fork': False}
        with self.assertRaises(APIError):scan(api, FORK)
        self.assertEqual(api.writes, [])

    def test_api_limit_is_not_reported_as_current(self):
        api = FakeAPI();original = api.call
        def call(method, path, body=None):
            if '/compare/' in path:raise APIError(429)
            return original(method, path, body)
        api.call = call
        row = next(r for r in scan(api, FORK)['branches'] if r['branch'] == 'feature/topic')
        self.assertEqual((row['status'], row['error']), ('unknown', '429'))

    def test_notice_escapes_branch_markdown(self):
        api = FakeAPI();api.ours['odd|`branch'] = A
        self.assertIn('`` odd\\|`branch ``', markdown(scan(api, FORK)))


class ForkNoticeSafetyTests(unittest.TestCase):
    def test_branch_names_render_as_code_not_mentions_or_markdown(self):
        api = FakeAPI();api.ours['feature/@someone'] = A
        self.assertIn('` feature/@someone `', markdown(scan(api, FORK)))


class ForkTransportTests(unittest.TestCase):
    def test_authentication_is_not_redirected_or_exposed_in_errors(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'https://untrusted.invalid'))
        api = GitHub(token='fixture-private-token')
        with patch.object(api.opener, 'open', side_effect=HTTPError('https://api.github.com', 302, 'fixture-private-token', {}, None)):
            with self.assertRaises(APIError) as failure:api.call('GET', '/repos/user/project')
        self.assertNotIn('fixture-private-token', str(failure.exception))

    def test_api_page_limit_fails_instead_of_silently_truncating(self):
        class Endless(GitHub):
            def __init__(self):pass
            def call(self, *args):return [{}] * 100
        with self.assertRaises(APIError):list(Endless().pages('/repos/user/project/branches'))


    def test_only_reads_retry_with_backoff_not_writes(self):
        from unittest.mock import patch
        api = GitHub(token='fixture')
        for method, count in [('GET', 3), ('POST', 1)]:
            with patch.object(api, '_request', side_effect=APIError('network_or_response')) as request, \
                 patch('scripts.fork_check.time.sleep') as sleep:
                with self.assertRaises(APIError):api.call(method, '/repos/user/project')
            self.assertEqual(request.call_count, count)
            self.assertEqual(sleep.call_count, count - 1)

    def test_rate_limit_stops_followup_requests_in_same_run(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        api = GitHub(token='fixture')
        with patch.object(api.opener, 'open', side_effect=HTTPError('https://api.github.com', 429, 'limit', {'Retry-After': '120'}, None)) as opened:
            with self.assertRaises(APIError):api.call('GET', '/repos/user/project')
            with self.assertRaises(APIError):api.call('GET', '/repos/user/project')
        self.assertEqual(opened.call_count, 1)
