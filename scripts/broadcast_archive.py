#!/usr/bin/env python3
"""Keep the two most recent bulletins and attach the homepage playlist."""
import datetime as dt
import json
from pathlib import Path
import re
import shutil

STEM = re.compile(r'^broadcasts/\d{8}T\d{6}Z\.(mp4|txt|vtt|srt)$')


def decorate_homepage(page):
    if 'id="broadcast-playlist"' in page:
        return page
    page = page.replace('</style>', '</style><link rel="stylesheet" href="playlist.css">', 1)
    page = re.sub(r'<p>Stand: ([^<]+)</p>', r'<p id="bulletin-timestamp">Stand: \1</p>', page, count=1)
    page = page.replace('<video controls', '<video id="bulletin-video" controls preload="metadata"', 1)
    page = page.replace("<h2>Quellen</h2><ul>", '<h2>Quellen</h2><ul id="bulletin-sources">', 1)
    page = page.replace("<a href='transcript.txt'>", "<a id='bulletin-transcript' href='transcript.txt'>", 1)
    page = page.replace("<a href='subtitles.de.srt'", "<a id='bulletin-subtitles' href='subtitles.de.srt'", 1)
    start = page.index('<video id="bulletin-video"')
    page = page[:start] + '''<main class="broadcast-layout"><section class="broadcast-player" aria-label="Ausgewählter Beitrag">
<h2 id="playing-title">Aktuelle Sendung</h2><p id="playing-kind" class="playing-kind">Sendung · Video</p>
<audio id="update-audio" controls preload="none" hidden></audio><div id="update-text" hidden></div>
''' + page[start:]
    page = page.replace('</html>', '''</section><aside id="broadcast-playlist" class="broadcast-playlist" aria-label="Playlist">
<div class="playlist-heading"><div><span class="playlist-eyebrow">PERSONALNEWSHOST</span><h2>Playlist</h2></div><span id="playlist-count" class="playlist-count"></span></div>
<p class="playlist-hint">Sendungen und Kurzupdates in zeitlicher Reihenfolge</p>
<ol id="playlist-items"><li class="playlist-empty">Playlist wird geladen …</li></ol>
<p id="playlist-status" class="playlist-status" role="status"></p>
</aside></main><script src="playlist.js"></script></html>''', 1)
    return page


def archive_broadcast(docs, published_at, title, sources):
    docs = Path(docs)
    stamp = dt.datetime.fromtimestamp(published_at, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base = 'broadcasts/' + stamp
    (docs / 'broadcasts').mkdir(exist_ok=True)
    entry = {'id': stamp, 'kind': 'broadcast', 'title': title,
             'created_at': published_at, 'video': base + '.mp4', 'sources': sources}
    for original, key, suffix in [('latest.mp4', 'video', '.mp4'), ('transcript.txt', 'transcript', '.txt'),
                                   ('subtitles.de.vtt', 'subtitles', '.vtt'), ('subtitles.de.srt', 'subtitle_download', '.srt')]:
        if (docs / original).is_file():
            shutil.copyfile(docs / original, docs / (base + suffix))
            entry[key] = base + suffix
    if not (docs / entry['video']).is_file():
        raise FileNotFoundError('Cannot archive a missing bulletin video')
    manifest = docs / 'broadcasts.json'
    old = json.loads(manifest.read_text()).get('broadcasts', []) if manifest.exists() else []
    entries = [e for e in old if e['id'] != stamp] + [entry]
    entries = sorted(entries, key=lambda e: e['created_at'])[-2:]
    keep = {e.get(key) for e in entries for key in ('video', 'transcript', 'subtitles', 'subtitle_download')}
    for asset in (docs / 'broadcasts').iterdir():
        relative = 'broadcasts/' + asset.name
        if asset.is_file() and STEM.fullmatch(relative) and relative not in keep:
            asset.unlink()
    manifest.write_text(json.dumps({'broadcasts': entries}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return entries
