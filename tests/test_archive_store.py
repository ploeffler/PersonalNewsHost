"""Broadcast archive: index, page and permanent store (T030)."""
import datetime as dt
import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts import archive_store as ar
from scripts.broadcast_archive import archive_broadcast


def ts(*args, zone=dt.timezone.utc):
    return dt.datetime(*args, tzinfo=zone).timestamp()


class Fixture:
    def __init__(self, tmp):
        self.docs = Path(tmp) / 'docs'
        self.store = Path(tmp) / 'archiv'
        self.docs.mkdir()

    def broadcast(self, when, video=b'video', title='Nachrichten'):
        (self.docs / 'latest.mp4').write_bytes(video)
        (self.docs / 'transcript.txt').write_text('Text ' + title)
        (self.docs / 'subtitles.de.vtt').write_text('WEBVTT\n')
        archive_broadcast(self.docs, when, title, [{'title': 'Q', 'url': 'https://orf.at/a'}])
        stamp = dt.datetime.fromtimestamp(when, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        (self.docs / 'artikel' / stamp).mkdir(parents=True, exist_ok=True)
        (self.docs / 'artikel' / stamp / '01-a.html').write_text('x')
        (self.docs / 'articles.json').write_text(json.dumps({'broadcast': stamp, 'articles': [
            {'title': 'Meldung <A>', 'path': f'artikel/{stamp}/01-a.html', 'sources': ['https://orf.at/a']}]}))
        return stamp


CONFIG = {'title': 'PNH', 'automation': {'timezone': 'Europe/Vienna'}}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = Fixture(self.tmp.name)

    def persist(self, config=CONFIG, with_store=True):
        env = {'PNH_ARCHIVE_PATH': str(self.f.store)} if with_store else {}
        return ar.persist_edition(self.f.docs, config, root=Path(self.tmp.name), env=env)

    def test_index_without_archive_path_is_metadata_only(self):
        self.f.broadcast(ts(2026, 11, 21, 6, 5))
        record = self.persist(with_store=False)
        self.assertFalse(record['archived'])
        self.assertFalse(self.f.store.exists())
        index = json.loads((self.f.docs / 'archive.json').read_text())['broadcasts']
        self.assertEqual(index[0]['stories'][0]['title'], 'Meldung <A>')
        self.assertEqual((index[0]['local_date'], index[0]['local_time'], index[0]['show']), ('2026-11-21', '07:05', 'main'))

    def test_permanent_copy_with_manifest_and_local_date(self):
        # 23:30 UTC on New Year's Eve is already 1 January in Vienna.
        stamp = self.f.broadcast(ts(2026, 12, 31, 23, 30), video=b'final video')
        record = self.persist({**CONFIG, 'show_id': 'technik'})
        folder = self.f.store / '2027' / '01' / '01' / 'technik' / stamp
        self.assertEqual((folder / 'video.mp4').read_bytes(), b'final video')
        manifest = json.loads((folder / 'manifest.json').read_text())
        self.assertEqual(manifest['files']['video.mp4']['sha256'], ar.sha256(folder / 'video.mp4'))
        self.assertEqual((manifest['timezone'], manifest['local_date']), ('Europe/Vienna', '2027-01-01'))
        self.assertTrue(manifest['created_utc'].startswith('2026-12-31T23:30'))
        self.assertEqual(record['archive_dir'], f'2027/01/01/technik/{stamp}')
        self.assertFalse(list(folder.glob('.*part')))

    def test_repeat_is_idempotent_and_conflicts_never_overwrite(self):
        stamp = self.f.broadcast(ts(2026, 11, 21, 11, 5), video=b'one')
        self.persist()
        self.persist()
        target = self.f.store / '2026/11/21/main' / stamp / 'video.mp4'
        self.assertEqual(target.read_bytes(), b'one')
        (self.f.docs / 'broadcasts' / f'{stamp}.mp4').write_bytes(b'changed')
        with self.assertRaises(ar.ArchiveError):
            self.persist()
        self.assertEqual(target.read_bytes(), b'one')

    def test_archived_videos_survive_rotation_of_public_copies(self):
        f = self.f  # persist after each broadcast, as generate.py does
        for d in (21, 22, 23):
            f.broadcast(ts(2026, 11, d, 6, 5), video=bytes([d]))
            self.persist()
        public = sorted(p.name for p in (f.docs / 'broadcasts').glob('*.mp4'))
        self.assertEqual(len(public), 2)  # temporary publication copies rotate
        archived = sorted(p.parent.name for p in f.store.rglob('video.mp4'))
        self.assertEqual(len(archived), 3)  # permanent copies stay
        index = json.loads((f.docs / 'archive.json').read_text())['broadcasts']
        self.assertEqual([r['local_date'] for r in index], ['2026-11-23', '2026-11-22', '2026-11-21'])

    def test_two_broadcasts_same_day_and_page_by_date(self):
        self.f.broadcast(ts(2026, 11, 21, 6, 5), title='Früh')
        self.persist()
        self.f.broadcast(ts(2026, 11, 21, 19, 5), title='Abend')
        self.persist()
        day = list((self.f.store / '2026/11/21/main').iterdir())
        self.assertEqual(len(day), 2)
        page = (self.f.docs / 'archive.html').read_text()
        self.assertIn('Samstag, 21.11.2026', page)
        self.assertLess(page.index('Abend'), page.index('Früh'))
        self.assertIn('Meldung &lt;A&gt;', page)
        self.assertIn('dauerhaft archiviert', page)
        self.assertIn("lang='de'", page)

    def test_missing_video_is_an_error_and_paths_are_safe(self):
        self.f.broadcast(ts(2026, 11, 21, 6, 5))
        with self.assertRaises(ar.ArchiveError):
            self.persist({**CONFIG, 'show_id': '../etc'})
        for video in (self.f.docs / 'broadcasts').glob('*.mp4'):
            video.unlink()
        with self.assertRaises(ar.ArchiveError):
            self.persist()

    def test_relative_archive_path_and_config(self):
        self.assertIsNone(ar.archive_root({}, env={}))
        self.assertEqual(ar.archive_root({'archive': {'path': 'archiv'}}, env={}, root=Path('/srv/pnh')),
                         Path('/srv/pnh/archiv'))
        self.assertEqual(ar.archive_root({'archive': {'path': 'x'}}, env={'PNH_ARCHIVE_PATH': '/data'}), Path('/data'))


class NoDeletionTests(unittest.TestCase):
    def test_archive_code_has_no_delete_operations_for_archived_files(self):
        source = (Path(__file__).resolve().parents[1] / 'scripts/archive_store.py').read_text()
        deletes = re.findall(r'\b(?:rmtree|rmdir|remove|unlink)\s*\(', source)
        # Only the temporary .part file is ever unlinked.
        self.assertEqual(deletes, ['unlink('])
        self.assertIn('temporary.unlink(missing_ok=True)', source)


if __name__ == '__main__':
    unittest.main()
