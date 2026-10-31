import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from scripts import security_checks as check


class SecurityChecksTests(unittest.TestCase):
    def test_large_artifact_and_chunk_boundary_do_not_hide_token(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'video.mp4'
            token='ghp_'+'A'*35
            p.write_bytes(b'x'*(65536*33-10)+token.encode())
            errors=check.scan_files([p],root=root,publication=True)
            self.assertEqual(len(errors),1)
            self.assertNotIn(token,str(errors))

    def test_known_private_values_and_authenticated_urls_are_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'report.json'
            for text in ['https://user:private@host.example/rss', 'https://host.example/rss?token=private', 'a private-contact-value leaked', '{"chat_id":"123456789"}']:
                p.write_text(text)
                self.assertTrue(check.scan_files([p],root=root,values=['private-contact-value'],publication=True))

    def test_private_state_and_escaping_symlink_cannot_be_uploaded(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            root=Path(d);private=root/'state';private.mkdir();p=private/'cache.sqlite';p.write_text('plain')
            target=Path(outside)/'private';target.write_text('plain');link=root/'report';link.symlink_to(target)
            self.assertEqual(len(check.scan_files([p,link],root=root,publication=True)),2)

    def test_public_news_is_preserved_but_trackers_are_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'index.html';p.write_text('<p>Öffentliche Nachrichten von Beispielquelle</p>')
            self.assertFalse(check.scan_files([p],root=root,publication=True))
            p.write_text('https://news.example/sport/sk-rapid-gewinnt-wichtiges-spiel-im-stadion')
            self.assertFalse(check.scan_files([p],root=root,publication=True))
            p.write_text('<script src="https://www.google-analytics.com/analytics.js"></script>')
            self.assertTrue(check.scan_files([p],root=root,publication=True))

    def test_config_fields_and_multiline_masks_are_extracted_without_model_data(self):
        config={'feeds':['https://user:private@host.example/rss'], 'telegram':{'chat_id':'123456789'}, 'title':'Public title', 'api_key':'abc\nxyz'}
        values=check.configuration_secrets(config)
        self.assertNotIn('Public title',values)
        self.assertIn('123456789',values)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'config.json';path.write_text(json.dumps(config))
            result=subprocess.run([sys.executable,str(check.ROOT/'scripts/security_checks.py'),'--mask-config',str(path)],capture_output=True,text=True,check=True)
            self.assertIn('::add-mask::abc%0Axyz',result.stdout)
            self.assertNotIn('\nxyz',result.stdout)

    def test_pinning_policy_rejects_mutable_actions_and_unbounded_packages(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.github/workflows').mkdir(parents=True)
            (root/'requirements.txt').write_text('jsonschema==4.19.2\n')
            (root/'requirements-constraints.txt').write_text('Pillow==12.1.1\n')
            p=root/'.github/workflows/test.yml'
            p.write_text('jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v5\n      - run: pip install unbounded\n')
            errors=check.pinning_errors(root)
            self.assertTrue(any('Action' in e for e in errors))
            self.assertTrue(any('constraint' in e for e in errors))

    def test_video_source_url_removes_credentials_query_and_fragment(self):
        self.assertEqual(check.public_source_url('https://user:private@host.example:8444/rss?token=private#fragment'), 'https://host.example:8444/rss')
        self.assertEqual(check.public_source_url('https://user:private@[::1]:8444/rss?token=private'), 'https://[::1]:8444/rss')

    def test_feed_failure_logs_do_not_expose_private_source_or_error(self):
        import contextlib
        import copy
        import io
        from unittest.mock import patch
        from scripts import generate
        cfg=copy.deepcopy(generate.CONFIG);cfg.pop('shows',None)
        cfg['feeds']=['https://user:private@host.example/rss?token=private']
        cfg['editorial']={'pipeline':{'enabled':False}}
        output=io.StringIO()
        with patch.object(generate,'CONFIG',cfg), patch.object(generate,'items_from_feed',side_effect=OSError('private exception details')), contextlib.redirect_stdout(output):
            with self.assertRaises(RuntimeError):generate.main()
        self.assertIn('OSError',output.getvalue())
        self.assertNotIn('private',output.getvalue())
        self.assertNotIn('host.example',output.getvalue())

    def test_current_repository_pins_and_artifact_guards(self):
        self.assertEqual(check.pinning_errors(),[])
        for path in (check.ROOT/'.github/workflows').glob('*.yml'):
            text=path.read_text()
            uploads=text.count('uses: actions/upload-artifact@')+text.count('uses: actions/upload-pages-artifact@')
            self.assertEqual(uploads,text.count('name: Check artifact publication boundary'),path.name)
            self.assertEqual(uploads,text.count(".outcome == 'success' }}"),path.name)

    def test_output_globs_scan_excluded_superset(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'out').mkdir();p=root/'out/.env';p.write_text('PRIVATE=example')
            files=check.output_files(['out/','!out/.env'],root)
            self.assertIn(p,files)
            self.assertTrue(check.scan_files(files,root=root,publication=True))

    def test_recursive_wildcards_include_hidden_files_and_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'out/.hidden/nested').mkdir(parents=True)
            expected = [root / 'out/.env', root / 'out/.hidden/nested/report.txt',
                        root / 'out/video.mp4']
            for path in expected:
                path.write_text('public')
            for pattern in ['out/**', 'out/**/*', 'out/*', str(root / 'out/**')]:
                with self.subTest(pattern=pattern):
                    self.assertTrue(set(expected) <= set(check.output_files([pattern], root)))
            self.assertEqual(check.output_files(['missing/**'], root), [])
