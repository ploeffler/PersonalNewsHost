import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.check_documentation_release import validate_release


class DocumentationReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'planning').mkdir()
        (self.root/'VERSION').write_text('0.1\n')
        self.marker={'version':'0.1','completed':True,'tests_passed':True,'branch':'Full-featured-Newsoutlet'}
        self.save()

    def save(self):
        (self.root/'planning/documentation-release.json').write_text(json.dumps(self.marker))

    def test_matching_confirmed_tag(self):
        self.assertEqual(validate_release('v0.1',self.root),'0.1')

    def test_incomplete_or_untested_blocks(self):
        for field in ('completed','tests_passed'):
            self.marker[field]=False;self.save()
            with self.assertRaises(ValueError):validate_release('v0.1',self.root)
            self.marker[field]=True

    def test_wrong_tag_or_branch_blocks(self):
        for tag in ('main','Full-featured-Newsoutlet','v0.2','v0.1;command'):
            with self.assertRaises(ValueError):validate_release(tag,self.root)
        self.marker['branch']='main';self.save()
        with self.assertRaises(ValueError):validate_release('v0.1',self.root)

    def test_unconfirmed_version_marker_blocks(self):
        self.marker.update(version=None,completed=False,tests_passed=False);self.save()
        with self.assertRaises(ValueError):validate_release('v0.1',self.root)

    def test_renderer_does_not_run_before_gate(self):
        from scripts import render_workflow_diagrams as renderer
        with patch('sys.argv',['render','--release-tag','v0.1']),patch.object(renderer,'validate_release',side_effect=ValueError('not complete')),patch.object(renderer.subprocess,'run') as run:
            with self.assertRaises(ValueError):renderer.main()
            run.assert_not_called()
