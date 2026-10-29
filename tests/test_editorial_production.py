import copy
import datetime as dt
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import wave
from unittest.mock import patch
from scripts import generate

class EditorialProductionTests(unittest.TestCase):
    def store(self,root,empty=False):
        now=dt.datetime.now(dt.timezone.utc).timestamp()
        sources=[] if empty else [
            {'id':'a','title':'Zugunglück in München: Zehn Menschen verletzt','text':'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Polizei ermittelt zur Ursache.','url':'https://first.org/a','first_seen_at':now-1,'published_at':now-1,'feed_urls':['https://first.org/rss']},
            {'id':'b','title':'Zugunglück in München: Zehn Menschen verletzt – Strecke gesperrt','text':'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Bahnstrecke bleibt bis zum Abend gesperrt.','url':'https://second.org/b','first_seen_at':now-2,'published_at':now-2,'feed_urls':['https://second.org/rss']}]
        (root/'docs').mkdir();(root/'docs/news-store.json').write_text(json.dumps({'updated_at':now,'articles':sources,'feeds':[]}))
        return now

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_stored_multi_source_text_reaches_voice_without_raw_refetch_or_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.store(root)
            cfg=copy.deepcopy(generate.CONFIG);cfg['station_logo']='';cfg['max_items']=1
            cfg['editorial']={'pipeline':{'enabled':True},'max_sentences':2}
            cfg['media']={'mode':'off'};cfg['presenter_settings']={'background':'assets/missing.jpg','scenes':{'intro_mode':'static','intro_static_type':'color','show_headlines':True}}
            spoken=[]
            def voice(text,path):
                spoken.append(text)
                with wave.open(str(path),'wb') as f:f.setparams((1,2,16000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*1600)
            with patch.object(generate,'ROOT',root),patch.object(generate,'DOCS',root/'docs'),patch.object(generate,'CONFIG',cfg),patch.object(generate,'synthesize',side_effect=voice),patch.object(generate,'items_from_feed',side_effect=AssertionError('raw feeds must not be read')),patch.object(generate,'extract_article_text',side_effect=AssertionError('text must not change after approval')),patch.object(generate,'crosscheck_headline',side_effect=AssertionError('old check must not run')):
                generate.main()
            report=json.loads((root/'docs/editorial-report.json').read_text());selected=[g for g in report['groups'] if g['selected']]
            self.assertEqual(len(selected),1);self.assertEqual(selected[0]['used_source_ids'],['a','b'])
            self.assertIn(selected[0]['draft']['text'],spoken)
            self.assertGreater((root/'docs/latest.mp4').stat().st_size,1000)
            groups=json.loads((root/'docs/story-groups.json').read_text());self.assertEqual(groups[0]['editorial_text'],selected[0]['draft']['text']);self.assertEqual(len(groups[0]['sources']),2)

    def test_later_text_tampering_blocks_voice_and_updates_audit(self):
        from scripts import editorial_pipeline
        original=editorial_pipeline.production_plan
        def tampered(*args,**kwargs):
            report,selected=original(*args,**kwargs)
            selected[0]['draft']['text']+=' Eine zusätzliche unbelegte Behauptung.'
            return report,selected
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.store(root)
            cfg=copy.deepcopy(generate.CONFIG);cfg['editorial']={'pipeline':{'enabled':True}}
            with patch.object(generate,'ROOT',root),patch.object(generate,'DOCS',root/'docs'),patch.object(generate,'CONFIG',cfg),patch.object(editorial_pipeline,'production_plan',side_effect=tampered),patch.object(generate,'synthesize') as voice:
                with self.assertRaises(RuntimeError):generate.main()
                voice.assert_not_called()
            report=json.loads((root/'docs/editorial-report.json').read_text())
            self.assertEqual(report['production_error'],'approval_invalidated_before_speech')
            self.assertEqual(report['groups'][0]['verification']['status'],'held')

    def test_no_approved_story_never_synthesizes_or_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.store(root,empty=True)
            cfg=copy.deepcopy(generate.CONFIG);cfg['editorial']={'pipeline':{'enabled':True}}
            with patch.object(generate,'ROOT',root),patch.object(generate,'DOCS',root/'docs'),patch.object(generate,'CONFIG',cfg),patch.object(generate,'synthesize') as voice,patch.object(generate,'items_from_feed') as fetch:
                with self.assertRaises(RuntimeError):generate.main()
                voice.assert_not_called();fetch.assert_not_called()
            self.assertTrue((root/'docs/editorial-report.json').exists())
            self.assertFalse((root/'docs/latest.mp4').exists())

if __name__=='__main__':unittest.main()
