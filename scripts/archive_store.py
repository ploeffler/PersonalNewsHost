"""Broadcast archive: JSON index, archive page and optional permanent video store (T030).

* Every finished broadcast is added to ``docs/archive.json`` (metadata only:
  date, show, stories, sources, video link) and listed on ``docs/archive.html``.
* If an archive path is configured (``archive.path`` or ``PNH_ARCHIVE_PATH``),
  the final video, transcript and subtitles are copied to
  ``<path>/YYYY/MM/DD/<show_id>/<broadcast_id>/`` together with a manifest
  (SHA-256, size, UTC time and time zone). The date is the local date in the
  show's time zone.
* Nothing in this module deletes archived files. Existing files are never
  overwritten; repeating the same archive step is a no-op. Only the temporary
  publication copies under ``docs/broadcasts/`` are rotated (broadcast_archive.py).
* An archive failure raises ``ArchiveError``; generate.py then keeps the last
  published edition.
"""
import datetime as dt
import hashlib
import html
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = (('video', 'video.mp4'), ('transcript', 'transcript.txt'),
         ('subtitles', 'subtitles.de.vtt'), ('subtitle_download', 'subtitles.de.srt'))
SAFE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')
WEEKDAYS = ('Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag')


class ArchiveError(RuntimeError):
    pass


def archive_root(config, env=None, root=ROOT):
    env = os.environ if env is None else env
    raw = env.get('PNH_ARCHIVE_PATH') or (config.get('archive') or {}).get('path') or ''
    if not str(raw).strip():
        return None
    path = Path(str(raw)).expanduser()
    return path if path.is_absolute() else Path(root) / path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def store_file(source, target):
    """Copy without ever overwriting: temp file, verify, then publish atomically."""
    source, target = Path(source), Path(target)
    expected = sha256(source)
    if target.exists():
        if sha256(target) == expected:
            return expected  # same archive step repeated
        raise ArchiveError(f'{target.name} already archived with different content')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f'.{target.name}.{os.getpid()}.part')
    try:
        with open(source, 'rb') as reader, open(temporary, 'wb') as writer:
            for block in iter(lambda: reader.read(1 << 20), b''):
                writer.write(block)
            writer.flush()
            os.fsync(writer.fileno())
        if temporary.stat().st_size != source.stat().st_size or sha256(temporary) != expected:
            raise ArchiveError(f'{target.name}: copy incomplete')
        try:
            os.link(temporary, target)  # fails if the target appeared meanwhile: no overwrite
        except FileExistsError:
            if sha256(target) != expected:
                raise ArchiveError(f'{target.name} already archived with different content') from None
        except OSError:
            if target.exists():
                raise ArchiveError(f'{target.name} appeared during archiving') from None
            os.replace(temporary, target)
    except OSError as exc:
        raise ArchiveError(f'Archive storage failed: {type(exc).__name__}') from exc
    finally:
        temporary.unlink(missing_ok=True)
    return expected


def _read(path, default):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def build_record(docs, config):
    docs = Path(docs)
    entries = _read(docs / 'broadcasts.json', {}).get('broadcasts', [])
    if not entries:
        raise ArchiveError('No broadcast to archive')
    entry = max(entries, key=lambda e: e['created_at'])
    show = str(config.get('show_id') or 'main')
    if not SAFE_ID.fullmatch(show) or not SAFE_ID.fullmatch(entry['id']):
        raise ArchiveError('Unsafe show or broadcast ID')
    zone_name = (config.get('automation') or {}).get('timezone') or 'UTC'
    local = dt.datetime.fromtimestamp(entry['created_at'], dt.timezone.utc).astimezone(ZoneInfo(zone_name))
    manifest = _read(docs / 'articles.json', {})
    stories = []
    if manifest.get('broadcast') == entry['id']:
        stories = [{'title': a['title'], 'page': a['path'], 'category': a.get('category'),
                    'sources': a.get('sources', [])} for a in manifest.get('articles', [])]
    return entry, {
        'id': entry['id'], 'show': show, 'title': entry.get('title', ''),
        'created_at': entry['created_at'],
        'created_utc': dt.datetime.fromtimestamp(entry['created_at'], dt.timezone.utc).isoformat(),
        'timezone': zone_name, 'local_date': local.date().isoformat(), 'local_time': local.strftime('%H:%M'),
        'stories': stories,
        'sources': [s.get('url') for s in entry.get('sources', []) if str(s.get('url', '')).startswith(('https://', 'http://'))],
        'video': entry.get('video'), 'archived': False}


def persist_edition(docs, config, root=ROOT, env=None):
    """Archive the newest broadcast of ``docs`` and refresh archive.json/archive.html."""
    docs = Path(docs)
    entry, record = build_record(docs, config)
    target_root = archive_root(config, env, root)
    if target_root is not None:
        day = record['local_date'].split('-')
        folder = target_root.joinpath(*day, record['show'], record['id'])
        files = {}
        for key, name in FILES:
            relative = entry.get(key)
            if relative and (docs / relative).is_file():
                files[name] = {'sha256': store_file(docs / relative, folder / name),
                               'bytes': (docs / relative).stat().st_size}
        if 'video.mp4' not in files:
            raise ArchiveError('Broadcast video missing; nothing archived')
        manifest = {**{k: v for k, v in record.items() if k not in ('video', 'archived')},
                    'files': files, 'archived_at': dt.datetime.now(dt.timezone.utc).isoformat()}
        manifest_path = folder / 'manifest.json'
        if not manifest_path.exists():
            temporary = folder / '.manifest.json.part'
            temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            os.replace(temporary, manifest_path)
        record.update(archived=True, archive_dir='/'.join([*day, record['show'], record['id']]))
    index = _read(docs / 'archive.json', {}).get('broadcasts', [])
    index = [r for r in index if not (r.get('id') == record['id'] and r.get('show') == record['show'])] + [record]
    index.sort(key=lambda r: r['created_at'], reverse=True)
    (docs / 'archive.json').write_text(json.dumps({'version': 1, 'broadcasts': index}, ensure_ascii=False, indent=1) + '\n',
                                       encoding='utf-8')
    (docs / 'archive.html').write_text(render_page(index, docs, config), encoding='utf-8')
    return record


def render_page(records, docs, config):
    """Static list of past broadcasts grouped by local date, newest first."""
    docs = Path(docs)
    esc = html.escape
    days = {}
    for record in records:
        days.setdefault(record['local_date'], []).append(record)
    sections = []
    for day in sorted(days, reverse=True):
        date = dt.date.fromisoformat(day)
        heading = f'{WEEKDAYS[date.weekday()]}, {date.strftime("%d.%m.%Y")}'
        items = []
        for record in sorted(days[day], key=lambda r: r['created_at'], reverse=True):
            links = []
            if record.get('video') and (docs / record['video']).is_file():
                links.append(f"<a href='{esc(record['video'], quote=True)}'>Video</a>")
            if record.get('archived'):
                links.append("<span class='badge'>dauerhaft archiviert</span>")
            stories = ''.join(
                (f"<li><a href='{esc(s['page'], quote=True)}'>{esc(s['title'])}</a></li>"
                 if s.get('page') and (docs / s['page']).is_file() else
                 f"<li>{esc(s['title'])}" + (f" – <a rel='noopener noreferrer' href='{esc(s['sources'][0], quote=True)}'>Quelle</a>"
                                             if s.get('sources') else '') + '</li>')
                for s in record.get('stories', []))
            items.append(
                f"<li class='archive-entry'><h3><time datetime='{esc(record['created_utc'])}'>{esc(record['local_time'])}</time> "
                f"{esc(record['title'])} <span class='show'>({esc(record['show'])})</span></h3>"
                + (f"<p>{' · '.join(links)}</p>" if links else '')
                + (f"<ul>{stories}</ul>" if stories else '') + '</li>')
        sections.append(f"<section aria-labelledby='day-{day}'><h2 id='day-{day}'>{esc(heading)}</h2>"
                        f"<ol class='archive-list'>{''.join(items)}</ol></section>")
    title = esc(str(config.get('title', 'PersonalNewsHost')))
    return ("<!doctype html><html lang='de'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Archiv – {title}</title><link rel='stylesheet' href='site.css'>"
            "<style>body{font:1.05rem/1.55 system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}"
            ".archive-list{list-style:none;padding:0}.archive-entry{border-top:1px solid var(--border);padding:.8rem 0}"
            ".archive-entry h3{font-size:1.05rem;margin:0 0 .3rem}.show{color:var(--muted);font-weight:400}"
            ".badge{font-size:.8rem;border:1px solid var(--border);border-radius:5px;padding:1px 6px;color:var(--muted)}</style>"
            "</head><body><main><nav><a href='index.html'>← Zur Startseite</a></nav>"
            f"<h1>Archiv</h1><p>{len(records)} Sendungen, nach Datum sortiert. Videos sind öffentlich nur für die "
            "letzten Sendungen abrufbar; dauerhaft archivierte Sendungen liegen im Archivspeicher des Betreibers.</p>"
            + (''.join(sections) or '<p>Noch keine Sendungen archiviert.</p>')
            + "</main><script src='theme.js'></script></body></html>\n")
