"""Automatic favicon refresh preserves usable cache data and merges job results safely."""
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from research.collect_source_logos import refresh_logos
from research.package_with_logos import package
from research.run import GROUPS

TODAY=dt.date(2026,11,5)

def png(color='red'):
    output=io.BytesIO();Image.new('RGB',(2,2),color).save(output,format='PNG');return output.getvalue()

def catalogue(root,hosts=('example.org',),group='news'):
    filename='feed-catalog.json' if group=='news' else 'police-feed-catalog.json'
    rows=[{'id':str(i),'url':'https://'+host+'/rss','publisher_country':'DE','format':'rss2','language':'de','status':'verified_recent','enabled_by_default':False} for i,host in enumerate(hosts)]
    data={'researched_on':'2026-11-05','feeds':rows,'counts':{'feeds':len(rows),'total_feeds':len(rows),'importable_feeds':len(rows)},'mixed_feeds':[],'non_feed_sources':[]}
    path=root/'docs'/filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))
    path.with_suffix('.opml').write_text('<opml><body>'+''.join('<outline xmlUrl="'+r['url']+'"/>' for r in rows)+'</body></opml>')

def cache(root,checked='2026-11-04',host='example.org',body=None):
    root.mkdir(parents=True,exist_ok=True)
    row={'icon':'assets/source-logos/abcd.png','status':'cached','source':'https://'+host+'/favicon.ico','site':'https://'+host+'/','checked_on':checked}
    (root/'abcd.png').write_bytes(body or png())
    (root/'index.json').write_text(json.dumps({host:row}))
    return row

def artifact(folder,group):
    for relative in GROUPS[group]['files']:
        target=folder/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('{}')
    catalogue(folder,(group+'.example',),group)
    (folder/'manifest.json').write_text(json.dumps({'group':group,'status':'success','mode':'live'}))
    (folder/'run.log').write_text(group+' research log')

class SourceLogoTests(unittest.TestCase):
    def test_fresh_cached_logo_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);cache(root/'cache')
            with patch('research.collect_source_logos.download_icon') as download:
                result=refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            download.assert_not_called();self.assertEqual(result['reused'],1)
            self.assertEqual((root/'out/abcd.png').read_bytes(),(root/'cache/abcd.png').read_bytes())

    def test_new_domain_is_downloaded_without_losing_other_group_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root,('new.example',));cache(root/'cache',host='existing.example')
            with patch('research.collect_source_logos.download_icon',return_value={'source':'https://new.example/icon.png','extension':'png','data':png('blue')}):
                result=refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            index=json.loads((root/'out/index.json').read_text())
            self.assertEqual(set(index),{'new.example','existing.example'});self.assertEqual(result['downloaded'],1)

    def test_expired_icon_is_refreshed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);cache(root/'cache',checked='2026-09-01')
            with patch('research.collect_source_logos.download_icon',return_value={'source':'https://example.org/new.png','extension':'png','data':png('blue')}):
                result=refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            row=json.loads((root/'out/index.json').read_text())['example.org']
            self.assertEqual(row['checked_on'],TODAY.isoformat());self.assertEqual(result['downloaded'],1)
            self.assertEqual((root/'out'/Path(row['icon']).name).read_bytes(),png('blue'))

    def test_transient_failure_keeps_previous_image_and_success_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);cache(root/'cache',checked='2026-09-01')
            with patch('research.collect_source_logos.download_icon',return_value=None):
                result=refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            row=json.loads((root/'out/index.json').read_text())['example.org']
            self.assertEqual(row['status'],'cached');self.assertEqual(row['checked_on'],'2026-09-01')
            self.assertEqual(row['last_attempt_on'],TODAY.isoformat());self.assertEqual(result['retained_after_error'],1)
            self.assertTrue((root/'out/abcd.png').exists())

    def test_missing_image_is_not_treated_as_a_usable_cache_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);cache(root/'cache');(root/'cache/abcd.png').unlink()
            with patch('research.collect_source_logos.download_icon',return_value=None) as download:
                refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            download.assert_called_once();row=json.loads((root/'out/index.json').read_text())['example.org']
            self.assertEqual(row['status'],'unavailable');self.assertNotIn('icon',row)

    def test_identical_images_share_one_local_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root,('one.example','two.example'))
            with patch('research.collect_source_logos.download_icon',return_value={'source':'https://icons.example/icon.png','extension':'png','data':png()}):
                refresh_logos(root,root/'out',root/'missing-cache',('news',),today=TODAY)
            index=json.loads((root/'out/index.json').read_text())
            self.assertEqual(len({r['icon'] for r in index.values()}),1)
            self.assertEqual(len(list((root/'out').glob('*.png'))),1)

    def test_refresh_does_not_replace_another_hosts_shared_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);row=cache(root/'cache',checked='2026-09-01')
            (root/'cache/index.json').write_text(json.dumps({'example.org':row,'other.example':dict(row)}))
            with patch('research.collect_source_logos.download_icon',return_value={'source':'https://example.org/new.png','extension':'png','data':png('blue')}):
                refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            index=json.loads((root/'out/index.json').read_text())
            self.assertNotEqual(index['example.org']['icon'],index['other.example']['icon'])
            self.assertEqual((root/'out'/Path(index['other.example']['icon']).name).read_bytes(),png())
            self.assertEqual((root/'out'/Path(index['example.org']['icon']).name).read_bytes(),png('blue'))

    def test_cache_paths_cannot_escape_asset_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);catalogue(root);row=cache(root/'cache');row['icon']='../secret.png'
            (root/'cache/index.json').write_text(json.dumps({'example.org':row}))
            with patch('research.collect_source_logos.download_icon',return_value=None):
                refresh_logos(root,root/'out',root/'cache',('news',),today=TODAY)
            self.assertNotIn('icon',json.loads((root/'out/index.json').read_text())['example.org'])

    def test_successful_groups_are_combined_before_one_shared_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact(root/'inputs/news','news');artifact(root/'inputs/authorities','authorities')
            with patch('research.package_with_logos.refresh_logos',return_value={'downloaded':0}) as refresh:
                result=package(root/'inputs',root/'out',root/'cache')
            self.assertEqual(set(result['groups']),{'news','authorities'});refresh.assert_called_once()
            self.assertEqual(set(refresh.call_args.kwargs['groups']),{'news','authorities'})
            self.assertTrue((root/'out/docs/feed-catalog.json').exists());self.assertTrue((root/'out/docs/police-feed-catalog.json').exists())
            self.assertEqual((root/'out/research-runs/news/run.log').read_text(),'news research log')
            self.assertEqual((root/'out/research-runs/authorities/run.log').read_text(),'authorities research log')

    def test_single_selected_group_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact(root/'inputs/news','news')
            with patch('research.package_with_logos.refresh_logos',return_value={}) as refresh:
                result=package(root/'inputs',root/'out',root/'cache')
            self.assertEqual(list(result['groups']),['news']);self.assertEqual(refresh.call_args.kwargs['groups'],('news',))
            self.assertFalse((root/'out/docs/police-feed-catalog.json').exists())

    def test_failed_second_group_does_not_replace_successful_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact(root/'inputs/news','news');artifact(root/'inputs/authorities','authorities')
            (root/'inputs/authorities/manifest.json').write_text(json.dumps({'group':'authorities','status':'failed'}))
            with patch('research.package_with_logos.refresh_logos',return_value={}) as refresh:
                result=package(root/'inputs',root/'out',root/'cache')
            self.assertEqual(list(result['groups']),['news'])
            self.assertEqual(refresh.call_args.kwargs['groups'],('news',))
            self.assertFalse((root/'out/docs/police-feed-catalog.json').exists())

    def test_failed_group_is_not_packaged_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact(root/'inputs/news','news')
            (root/'inputs/news/manifest.json').write_text(json.dumps({'group':'news','status':'failed'}))
            with patch('research.package_with_logos.refresh_logos') as refresh:
                with self.assertRaisesRegex(ValueError,'No successful'):package(root/'inputs',root/'out')
            refresh.assert_not_called();self.assertEqual(json.loads((root/'out/manifest.json').read_text())['status'],'failed')
            self.assertFalse((root/'out/docs').exists())

if __name__=='__main__':unittest.main()
