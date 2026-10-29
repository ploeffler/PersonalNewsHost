import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from short_update_video import render_short_update
from video_branding import apply_branding

class ShortUpdateVideoTests(unittest.TestCase):
    def test_branding_rejects_path_traversal(self):
        with self.assertRaises(ValueError):apply_branding([],[],'0:v',ROOT,{'station_logo':'assets/../secret.png'})

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg needed')
    def test_render_has_video_audio_red_label_and_transparent_logo(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'assets').mkdir()
            logo=Image.new('RGBA',(160,90),(0,0,0,0));logo.paste((0,255,0,255),(80,0,160,90));logo.save(root/'assets/logo-video.png')
            audio=root/'voice.wav'
            with wave.open(str(audio),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b'\0\0'*16000)
            output=root/'update.mp4'
            render_short_update({'title':'Beschluss bestätigt','text':'Das Parlament hat den Beschluss bestätigt.','created_at':1700000000,'source':'example.org'},audio,output,root,{})
            metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
            self.assertEqual({s['codec_type'] for s in metadata['streams']},{'video','audio'})
            video=next(s for s in metadata['streams'] if s['codec_type']=='video');self.assertEqual((video['width'],video['height']),(1280,720))
            frame=root/'frame.png';subprocess.run(['ffmpeg','-v','error','-y','-i',str(output),'-frames:v','1',str(frame)],check=True)
            im=Image.open(frame).convert('RGB')
            # Transparent left half of the logo shows the studio background.
            pixel=im.getpixel((1100,40));self.assertLess(max(pixel)-min(pixel),60)
            red=sum(1 for y in range(50,100) for x in range(870,1080) if (lambda c:c[0]>130 and c[0]>c[1]*1.6 and c[0]>c[2]*1.6)(im.getpixel((x,y))))
            self.assertGreater(red,200)
            green=im.getpixel((1230,60));self.assertGreater(green[1],150)

class ShortUpdateVideoRetentionTests(unittest.TestCase):
    def test_existing_audio_gets_one_video_and_expiry_removes_both(self):
        import time, types
        from unittest.mock import patch, Mock
        spec=importlib.util.spec_from_file_location('short_updates_integration',ROOT/'scripts/short_updates.py')
        updates=importlib.util.module_from_spec(spec);spec.loader.exec_module(updates)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);docs=root/'docs';audio=docs/'short-update-audio';audio.mkdir(parents=True)
            item={'id':'a'*24,'title':'Ein Kurzupdate','text':'Ein vollständiger Satz.','created_at':time.time()-10,'audio':'short-update-audio/'+'a'*24+'.wav'}
            (audio/('a'*24+'.wav')).write_bytes(b'audio fixture')
            state=docs/'short-update-state.json';state.write_text(json.dumps({'updates':[item],'seen':{}}))
            news=types.SimpleNamespace(CONFIG={'feeds':[]},feed_timestamp=lambda n:0,ATOM='{atom}')
            render=Mock(side_effect=lambda update,audio,output,*args:Path(output).write_bytes(b'video fixture'))
            video_module=types.SimpleNamespace(render_short_update=render)
            with patch.object(updates,'ROOT',root),patch.dict(sys.modules,{'generate':news,'scripts.short_update_video':video_module,'short_update_video':video_module}):
                updates.main();updates.main()
                self.assertEqual(render.call_count,1)
                public=json.loads((docs/'short-updates.json').read_text())['updates'][0]
                self.assertTrue((docs/public['video']).is_file())
                expired=json.loads(state.read_text());expired['updates'][0]['created_at']=time.time()-86401;state.write_text(json.dumps(expired))
                updates.main()
            self.assertFalse(list(audio.glob('*.wav')))
            self.assertFalse(list((docs/'short-update-video').glob('*.mp4')))
            self.assertFalse(json.loads((docs/'short-updates.json').read_text())['updates'])

if __name__=='__main__':unittest.main()
