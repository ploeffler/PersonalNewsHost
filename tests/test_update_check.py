"""T195: public upstream discovery and private, non-installing update status."""
import base64
import copy
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import update_check as updater

A, B = 'a' * 40, 'b' * 40


class UpdateCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'VERSION').write_text('0.1\n')
        self.identity = dict(version='0.1', commit=A, tag='v0.1', local_changes=False,
                             image_digest=None, identity_source='checkout')
        self.tags = [{'name': 'v0.2', 'commit': {'sha': B}}, {'name': 'v0.1', 'commit': {'sha': A}}]
        self.calls = []
        self.markers = {B: '0.2', A: '0.1'}
        self.release_flags = {}

    def get(self, url):
        self.calls.append(url)
        if '/tags?' in url:return copy.deepcopy(self.tags)
        if '/contents/VERSION?' in url:
            return {'encoding': 'base64', 'content': base64.b64encode(self.markers[url.split('=')[-1]].encode()).decode()}
        if '/releases/tags/' in url:return dict(body='Public notes', **self.release_flags)
        commit = url.split('/')[-3]
        return {'version': self.markers[commit], 'completed': True, 'tests_passed': True,
                'branch': 'Full-featured-Newsoutlet'}

    def check(self, **kwargs):
        with patch.object(updater, 'installed', return_value=self.identity):
            return updater.check(self.root, get=self.get, **kwargs)

    def test_semantic_order_and_prerelease_order(self):
        self.assertGreater(updater.version_key('v0.10'), updater.version_key('v0.9'))
        self.assertEqual(updater.version_key('v0.1'), updater.version_key('v0.1.0'))
        for low, high in [('v1.0.0-alpha.2', 'v1.0.0-alpha.10'), ('v1.0.0-rc.1', 'v1.0.0')]:
            self.assertLess(updater.version_key(low), updater.version_key(high))
        for value in ['v01.2', 'v1.2-rc.01', 'main', 'v1.2;command']:
            with self.assertRaises(updater.CheckError):updater.version_key(value)

    def test_original_source_new_version_and_private_status(self):
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'private-fixture-token'}):
            result = self.check(now=100)
        self.assertTrue(result['update_available'])
        self.assertEqual(result['latest_release']['commit'], B)
        self.assertTrue(all('/ploeffler/PersonalNewsHost/' in url for url in self.calls))
        data = (self.root / 'state/updates/check.json').read_text()
        self.assertNotIn('private-fixture-token', data)
        self.assertEqual(stat.S_IMODE((self.root / 'state/updates/check.json').stat().st_mode), 0o600)
        self.assertEqual((self.root / 'VERSION').read_text(), '0.1\n')

    def test_equal_and_older_versions_do_not_update(self):
        for version in ['0.2', '0.3']:
            self.identity['version'] = version
            self.assertFalse(self.check(now=100, force=True)['update_available'])

    def test_stable_filters_prerelease_and_unreleased_marker(self):
        self.tags.insert(0, {'name': 'v9.0-rc.1', 'commit': {'sha': 'c' * 40}})
        self.assertEqual(self.check(now=100)['latest_release']['tag'], 'v0.2')
        self.assertNotIn('c' * 40, ' '.join(self.calls))
        def unconfirmed(url):
            result = self.get(url)
            if url.startswith(updater.RAW + '/' + B):result['completed'] = False
            return result
        with patch.object(updater, 'installed', return_value=self.identity):
            result = updater.check(self.root, force=True, get=unconfirmed, now=200)
        self.assertFalse(result['update_available'])
        self.assertEqual(result['latest_release']['tag'], 'v0.1')

    def test_draft_and_prerelease_release_objects_are_excluded(self):
        for flag in ['draft', 'prerelease']:
            self.release_flags = {flag: True}
            self.assertIsNone(self.check(now=100, force=True)['latest_release'])

    def test_tag_without_github_release_still_requires_confirmed_marker(self):
        def tag_only(url):
            if '/releases/tags/' in url:raise HTTPError(url, 404, 'not found', {}, None)
            return self.get(url)
        with patch.object(updater, 'installed', return_value=self.identity):
            result = updater.check(self.root, get=tag_only, now=100)
        self.assertTrue(result['update_available'])

    def test_changed_tag_is_not_silently_accepted_across_restart(self):
        self.check(now=100)
        self.tags[0]['commit']['sha'] = 'c' * 40
        result = self.check(now=200, force=True)
        self.assertEqual(result['error'], 'tag_changed')
        self.assertFalse(result['update_available'])
        self.assertEqual(result['last_success_at'], 100)
        self.assertEqual(result['seen_tags']['v0.2'], B)

    def test_offline_and_rate_limits_keep_last_success_and_backoff(self):
        self.check(now=100)
        with patch.object(updater, 'installed', return_value=self.identity):
            for failure in [OSError('private-error-content'), HTTPError('private-url', 429, 'private', {'Retry-After': '3600'}, None)]:
                with patch.object(self, 'get', side_effect=failure):
                    result = updater.check(self.root, force=True, get=self.get, now=200)
                self.assertFalse(result['update_available'])
                self.assertEqual(result['last_success_at'], 100)
                self.assertNotIn('private', json.dumps(result))
                self.assertGreater(result['next_check_at'], 200)
        self.assertGreaterEqual(result['next_check_at'], 3800)

    def test_interval_survives_process_restart(self):
        self.check(now=100)
        self.calls.clear()
        self.assertEqual(self.check(now=101)['last_attempt_at'], 100)
        self.assertEqual(self.calls, [])
        self.check(now=86501)
        self.assertTrue(self.calls)

    def test_new_installed_identity_invalidates_cached_availability(self):
        self.assertTrue(self.check(now=100)['update_available'])
        self.identity['version'] = '0.2'
        self.calls.clear()
        self.assertFalse(self.check(now=101)['update_available'])
        self.assertTrue(self.calls)

    def test_development_channel_requires_explicit_selection(self):
        self.tags.insert(0, {'name': 'v0.3-rc.1', 'commit': {'sha': 'c' * 40}})
        self.markers['c' * 40] = '0.3-rc.1'
        self.assertEqual(self.check(now=100)['latest_release']['tag'], 'v0.2')
        self.assertEqual(self.check(now=101, channel='development')['latest_release']['tag'], 'v0.3-rc.1')

    def test_release_version_mismatch_fails_closed(self):
        def mismatch(url):
            result = self.get(url)
            if '/contents/VERSION?' in url:result['content'] = base64.b64encode(b'99.0').decode()
            return result
        with patch.object(updater, 'installed', return_value=self.identity):
            result = updater.check(self.root, get=mismatch, now=100)
        self.assertEqual(result['error'], 'release_version_mismatch')

    def test_container_identity_accepts_only_matching_version_commit_and_digest(self):
        info = dict(version='0.1', commit=A, tag='v0.1', image_digest='sha256:' + 'd' * 64)
        path = self.root / 'build-info.json';path.write_text(json.dumps(info))
        self.assertEqual(updater.installed(self.root)['image_digest'], info['image_digest'])
        info['version'] = '0.2';path.write_text(json.dumps(info))
        with self.assertRaises(updater.CheckError):updater.installed(self.root)

    def test_watch_repeats_without_installation_and_stops_cleanly(self):
        value = {'next_check_at': 100, 'error': None}
        with patch.object(updater, 'check', return_value=value) as check, \
             patch.object(updater.time, 'sleep', side_effect=[None, KeyboardInterrupt]), \
             patch('builtins.print'):
            self.assertEqual(updater.main(['--watch']), 0)
        self.assertEqual(check.call_count, 2)
