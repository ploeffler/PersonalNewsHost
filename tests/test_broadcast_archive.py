import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('broadcast_archive',Path(__file__).resolve().parents[1]/'scripts/broadcast_archive.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class BroadcastArchiveTests(unittest.TestCase):
    def test_two_broadcasts_and_their_sidecars_survive_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            docs=Path(directory)
            for i in range(3):
                (docs/'latest.mp4').write_bytes(str(i).encode())
                (docs/'transcript.txt').write_text('Transcript '+str(i))
                (docs/'subtitles.de.vtt').write_text('WEBVTT '+str(i))
                entries=m.archive_broadcast(docs,1700000000+i*3600,'Sendung '+str(i),[{'title':'Quelle','url':'https://example.org/'}])
            self.assertEqual(len(entries),2)
            self.assertEqual([e['title'] for e in entries],['Sendung 1','Sendung 2'])
            self.assertEqual(len(list((docs/'broadcasts').glob('*.mp4'))),2)
            self.assertEqual((docs/entries[0]['video']).read_bytes(),b'1')
            self.assertEqual((docs/entries[0]['transcript']).read_text(),'Transcript 1')
            self.assertEqual(len(m.archive_broadcast(docs,1700007200,'Retry',[])),2)
            (docs/'broadcasts/notes.txt').write_text('Keep')
            m.archive_broadcast(docs,1700010800,'Next',[])
            self.assertTrue((docs/'broadcasts/notes.txt').exists())

    def test_missing_video_does_not_publish_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):m.archive_broadcast(Path(directory),1700000000,'Missing',[])
            self.assertFalse((Path(directory)/'broadcasts.json').exists())

    def test_homepage_is_decorated_once(self):
        page="<html><style></style><p>Stand: Heute</p><video controls></video><h2>Quellen</h2><ul></ul></html>"
        result=m.decorate_homepage(page)
        self.assertIn('id="broadcast-playlist"',result)
        self.assertIn('id="bulletin-video"',result)
        self.assertEqual(m.decorate_homepage(result),result)

if __name__=='__main__':unittest.main()
