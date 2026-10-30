"""Research artifacts must remain reviewable and must never silently activate sources."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from research.run import run_group,GROUPS
from research.validate_catalogs import validate


def fixture(root,group='news',warning=False):
    stem='feed-catalog' if group=='news' else 'police-feed-catalog'
    row={'id':'one','url':'https://example.org/feed','language':'de','format':'rss2',
         'status':'available_empty' if warning else 'verified_recent','enabled_by_default':False}
    if warning:row.update(purpose='official_warning',requires_warning_adapter=True)
    data={'researched_on':'2026-10-28','feeds':[row],
          'counts':{'feeds':1,'total_feeds':1,'importable_feeds':1},'mixed_feeds':[],'non_feed_sources':[]}
    for relative in GROUPS[group]['files']:
        p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
    (root/'docs'/f'{stem}.json').write_text(json.dumps(data))
    opml=ET.Element('opml');body=ET.SubElement(opml,'body')
    ET.SubElement(body,'outline',xmlUrl=row['url'])
    ET.ElementTree(opml).write(root/'docs'/f'{stem}.opml')
    return data


class FeedResearchTests(unittest.TestCase):
    def test_stored_catalogues_validate(self):
        for group in GROUPS:
            with self.subTest(group=group):
                result=validate(group)
                self.assertGreater(result['feeds'],0)
                self.assertGreater(result['opml_feeds'],0)

    def test_empty_catalogue_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=fixture(root);data['feeds']=[]
            (root/'docs/feed-catalog.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'empty'):
                validate('news',root)

    def test_duplicates_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=fixture(root);data['feeds']*=2
            (root/'docs/feed-catalog.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                validate('news',root)

    def test_research_cannot_activate_a_feed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=fixture(root);data['feeds'][0]['enabled_by_default']=True
            (root/'docs/feed-catalog.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'activate'):
                validate('news',root)

    def test_opml_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            (root/'docs/feed-catalog.opml').write_text('<opml><body/></opml>')
            with self.assertRaisesRegex(ValueError,'OPML'):
                validate('news',root)

    def test_empty_warning_feed_is_valid_with_adapter_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root,'authorities',warning=True)
            self.assertEqual(validate('authorities',root)['opml_feeds'],1)

    def test_warning_adapter_requirement_cannot_be_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=fixture(root,'authorities',warning=True)
            data['feeds'][0]['requires_warning_adapter']=False
            (root/'docs/police-feed-catalog.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'adapter'):
                validate('authorities',root)

    def test_failed_run_exports_failure_log_but_no_old_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);output=root/'artifact'
            failed=subprocess.CompletedProcess(['python'],1,'Network unavailable')
            with patch('research.run.subprocess.run',return_value=failed):
                with self.assertRaises(subprocess.CalledProcessError):
                    run_group('news',output,root=root)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['status'],'failed')
            self.assertEqual(manifest['mode'],'live')
            self.assertIn('Network unavailable',(output/'run.log').read_text())
            self.assertFalse((output/'docs').exists())

    def test_offline_export_is_labelled_as_stored_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);output=root/'artifact'
            ok=subprocess.CompletedProcess(['python'],0,'Rebuilt stored sources')
            with patch('research.run.subprocess.run',return_value=ok) as proc:
                manifest=run_group('news',output,offline=True,root=root)
            self.assertEqual(proc.call_count,1)
            self.assertEqual(manifest['mode'],'stored_snapshot')
            self.assertEqual(manifest['status'],'success')
            self.assertEqual(manifest['validation']['researched_on'],'2026-10-28')
            self.assertTrue((output/'docs/feed-catalog.json').exists())
            self.assertTrue((output/'research/rss/feed-research-raw.json').exists())

    def test_existing_artifact_directory_is_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                run_group('news',Path(tmp),root=Path(tmp))


if __name__=='__main__':unittest.main()
