"""Suchindex für die clientseitige Volltextsuche (T031).

``docs/search-index.json`` enthält Meldungen (Titel, Kurztext, Rubrik, Quelle)
und Sendungen (Titel, Datum, Beiträge). Die Suche läuft vollständig im Browser
(``docs/search.js``); es gibt keinen Serveraufruf und keinen externen Dienst.
Die Größe ist begrenzt (``search.max_bytes``, Standard 1 MB): zuerst entfallen
die ältesten Einträge.
"""
import json
from pathlib import Path

try:
    from scripts import homepage as _home
    from scripts import section_pages as _sections
except ModuleNotFoundError:
    import homepage as _home
    import section_pages as _sections

DEFAULT_MAX_BYTES = 1_000_000
MIN_MAX_BYTES = 10_000
TEXT_LIMIT = 240
MAX_ARTICLES = 2000


def settings_from(config):
    raw = (config.get('search') or {}) if isinstance(config, dict) else {}
    limit = raw.get('max_bytes', DEFAULT_MAX_BYTES)
    limit = limit if isinstance(limit, int) and not isinstance(limit, bool) and limit >= MIN_MAX_BYTES else DEFAULT_MAX_BYTES
    return {'enabled': raw.get('enabled', True) is not False, 'max_bytes': limit}


def _clip(text, limit=TEXT_LIMIT):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + ' …'


def _size(index):
    return len(json.dumps(index, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def build_index(config, store, archive, manifest, now, max_bytes=None):
    max_bytes = max_bytes or settings_from(config)['max_bytes']
    settings, sections = _sections.sections_of(config)
    labels = {raw: label for _, label, raw in sections}
    links = _home._article_links(manifest)
    entries = []
    for article in store.get('articles', [])[:MAX_ARTICLES]:
        if not article.get('title') or not _home._safe(article.get('url', '')):
            continue
        raw = _home._section_of(article, settings)
        stamp = article.get('published_at') or article.get('first_seen_at') or 0
        entries.append({'k': 'a', 'title': _clip(article['title'], 200), 'text': _clip(article.get('text')),
                        'section': labels.get(raw, ''), 'source': _home._host(article['url']),
                        'url': links.get(article['title']) or article['url'], 'date': int(stamp)})
    for record in archive.get('broadcasts', []):
        video = record.get('video')
        entries.append({'k': 'b', 'title': _clip(record.get('title'), 200),
                        'text': _clip(' · '.join(s.get('title', '') for s in record.get('stories', []))),
                        'section': str(record.get('show', '')), 'source': '',
                        'url': video if video else 'archive.html', 'date': int(record.get('created_at', 0))})
    entries.sort(key=lambda e: e['date'], reverse=True)
    index = {'version': 1, 'generated_at': int(now), 'truncated': False, 'entries': entries}
    while entries and _size(index) > max_bytes:
        keep = len(entries) * 9 // 10 if len(entries) > 10 else len(entries) - 1
        del entries[keep:]
        index['truncated'] = True
    return index


def write_index(docs, config, store=None, archive=None, manifest=None, now=0):
    docs = Path(docs)
    if not settings_from(config)['enabled']:
        return None

    def read(name, default):
        try:
            return json.loads((docs / name).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return default
    index = build_index(config, read('news-store.json', {}) if store is None else store,
                        read('archive.json', {}) if archive is None else archive,
                        read('articles.json', {}) if manifest is None else manifest, now)
    target = docs / 'search-index.json'
    text = json.dumps(index, ensure_ascii=False, separators=(',', ':'))
    if not target.is_file() or target.read_text(encoding='utf-8') != text:
        target.write_text(text, encoding='utf-8')
    return index
