"""Rubriken- und Sendungsseiten mit Paginierung (T022).

Je konfigurierter Rubrik (``editorial.broadcast_sections.sections``) entsteht
``docs/rubrik/<id>/index.html`` und je Sendung ``docs/sendung/<id>/index.html``;
weitere Seiten heißen ``page-2.html`` usw. Die Seiten sind statisch (kein
JavaScript nötig), verlinken sich über Breadcrumbs und eine Navigation
untereinander und werden bei jedem RSS-Lauf und jeder Sendung neu erzeugt
(``homepage.update_homepage``).

* Rubrikenseiten: Meldungen aus ``docs/news-store.json``, neueste zuerst. Die
  Zuordnung zur Rubrik ist dieselbe wie auf der Startseite.
* Sendungsseiten: Sendungen aus ``docs/archive.json`` (T030), neueste zuerst.
  Ohne ``shows`` in der Konfiguration gibt es die Sendung ``main``.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from scripts import homepage as _home
except ModuleNotFoundError:  # script run from the scripts folder
    import homepage as _home

PAGE_SIZE = 20
MAX_ARTICLES = 500
SECTION_DIR, SHOW_DIR = 'rubrik', 'sendung'
SAFE = re.compile(r'[^a-z0-9-]+')
PAGE_FILE = re.compile(r'page-\d+\.html')


def safe_id(value):
    return SAFE.sub('-', str(value).lower()).strip('-')[:64]


def page_name(number):
    return 'index.html' if number == 1 else f'page-{number}.html'


def paginate(items, size=PAGE_SIZE):
    return [items[i:i + size] for i in range(0, len(items), size)] or [[]]


def sections_of(config):
    settings = (config.get('editorial', {}) or {}).get('broadcast_sections', {}) or {}
    sections = settings.get('sections') or [{'id': 'general', 'label': 'Allgemein'}]
    result, seen = [], set()
    for section in sections:
        ident = safe_id(section.get('id', ''))
        if ident and ident not in seen:
            seen.add(ident)
            result.append((ident, str(section.get('label') or section.get('id')), section.get('id')))
    return settings, result


def shows_of(config):
    shows = config.get('shows')
    if not isinstance(shows, list) or not shows:
        return [('main', str(config.get('title', 'PersonalNewsHost')), 'main')]
    result, seen = [], set()
    for show in shows:
        if not isinstance(show, dict):
            continue
        ident = safe_id(show.get('id', ''))
        if ident and ident not in seen:
            seen.add(ident)
            result.append((ident, str(show.get('title') or show.get('id')), show.get('id')))
    return result


def _shell(title, site, crumbs, body, nav):
    esc = html.escape
    trail = ' › '.join(f"<a href='{esc(href, quote=True)}'>{esc(label)}</a>" for label, href in crumbs[:-1])
    trail += (' › ' if trail else '') + f"<span aria-current='page'>{esc(crumbs[-1][0])}</span>"
    return ("<!doctype html><html lang='de'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)} – {esc(site)}</title><link rel='stylesheet' href='../../site.css'>"
            "<style>body{font:1.05rem/1.55 system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}"
            ".crumbs,.sitenav,.pager{font-size:.9rem;margin:.6rem 0}.sitenav ul,.pager ul{list-style:none;display:flex;"
            "flex-wrap:wrap;gap:.4rem 1rem;padding:0;margin:.3rem 0}.page-list{list-style:none;padding:0}"
            ".page-list li{border-top:1px solid var(--border);padding:.6rem 0}</style></head><body><main>"
            f"<nav class='crumbs' aria-label='Brotkrumen'>{trail}</nav><h1>{esc(title)}</h1>{body}{nav}"
            "</main><script src='../../theme.js'></script></body></html>\n")


def _sitenav(sections, shows, current):
    def links(kind, entries, folder):
        return ''.join(
            f"<li><a href='../../{folder}/{ident}/index.html'" + (" aria-current='page'" if (kind, ident) == current else '')
            + f'>{html.escape(label)}</a></li>' for ident, label, _ in entries)
    return ("<nav class='sitenav' aria-label='Rubriken und Sendungen'>"
            f"<strong>Rubriken</strong><ul>{links('section', sections, SECTION_DIR)}</ul>"
            f"<strong>Sendungen</strong><ul>{links('show', shows, SHOW_DIR)}</ul></nav>")


def _pager(number, total):
    if total <= 1:
        return ''
    items = []
    if number > 1:
        items.append(f"<li><a rel='prev' href='{page_name(number - 1)}'>← Neuere</a></li>")
    items.append(f"<li>Seite {number} von {total}</li>")
    if number < total:
        items.append(f"<li><a rel='next' href='{page_name(number + 1)}'>Ältere →</a></li>")
    return f"<nav class='pager' aria-label='Seiten'><ul>{''.join(items)}</ul></nav>"


def _write_pages(folder, pages, render, remove_old=True):
    folder.mkdir(parents=True, exist_ok=True)
    for number, items in enumerate(pages, 1):
        (folder / page_name(number)).write_text(render(number, items, len(pages)), encoding='utf-8')
    if remove_old:
        for path in folder.glob('page-*.html'):
            if PAGE_FILE.fullmatch(path.name) and int(path.name[5:-5]) > len(pages):
                path.unlink()


def _article_item(article, links, zone):
    published = article.get('published_at') or article.get('first_seen_at') or 0
    local = dt.datetime.fromtimestamp(published, dt.timezone.utc).astimezone(zone)
    page = links.get(article['title'])
    href, extra = (f'../../{page}', '') if page else (article['url'], " rel='noopener noreferrer'")
    return (f"<li><a href='{html.escape(href, quote=True)}'{extra}>{html.escape(article['title'])}</a>"
            f"<span class='block-meta'>{html.escape(_home._host(article['url']))} · "
            f"<time datetime='{local.isoformat()}'>{local.strftime('%d.%m.%Y, %H:%M')}</time></span></li>")


def _broadcast_item(record, docs):
    esc = html.escape
    links = []
    video = record.get('video')
    if video and (docs / video).is_file():
        links.append(f"<a href='../../{esc(video, quote=True)}'>Video</a>")
    stories = ''.join(
        (f"<li><a href='../../{esc(s['page'], quote=True)}'>{esc(s['title'])}</a></li>"
         if s.get('page') and (docs / s['page']).is_file() else f"<li>{esc(s.get('title', ''))}</li>")
        for s in record.get('stories', []))
    return (f"<li><h3><time datetime='{esc(record.get('created_utc', ''))}'>{esc(record.get('local_date', ''))} "
            f"{esc(record.get('local_time', ''))}</time> {esc(record.get('title', ''))}</h3>"
            + (f"<p>{' · '.join(links)}</p>" if links else '') + (f'<ul>{stories}</ul>' if stories else '') + '</li>')


def build_section_pages(docs, config, store=None, archive=None, manifest=None, now=None):
    """Write all Rubriken- and Sendungsseiten of ``docs``; returns the list of written index paths."""
    docs = Path(docs)

    def read(name, default):
        try:
            return json.loads((docs / name).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return default
    store = read('news-store.json', {}) if store is None else store
    archive = read('archive.json', {}) if archive is None else archive
    manifest = read('articles.json', {}) if manifest is None else manifest
    settings, sections = sections_of(config)
    shows = shows_of(config)
    site = str(config.get('title', 'PersonalNewsHost'))
    zone = ZoneInfo((config.get('automation') or {}).get('timezone') or 'Europe/Vienna')
    links = _home._article_links(manifest)
    valid = {s.get('id') for s in settings.get('sections', [])}
    by_section = {ident: [] for ident, _, _ in sections}
    articles = [a for a in store.get('articles', []) if a.get('title') and _home._safe(a.get('url', ''))]
    articles.sort(key=lambda a: a.get('published_at') or a.get('first_seen_at') or 0, reverse=True)
    raw_to_safe = {raw: ident for ident, _, raw in sections}
    for article in articles[:MAX_ARTICLES]:
        raw = _home._section_of(article, settings) if valid else sections[0][2]
        ident = raw_to_safe.get(raw) or safe_id(raw)
        if ident in by_section:
            by_section[ident].append(article)
    written = []
    for ident, label, _ in sections:
        def render_section(number, items, total, ident=ident, label=label):
            body = (f"<p>{len(by_section[ident])} Meldungen in dieser Rubrik.</p><ul class='page-list'>"
                    + ''.join(_article_item(a, links, zone) for a in items) + '</ul>') if items else \
                "<p class='block-empty'>In dieser Rubrik liegen noch keine Meldungen vor.</p>"
            crumbs = [('Start', '../../index.html'), ('Rubriken', f'../../index.html#ressorts'), (label, page_name(number))]
            return _shell(label, site, crumbs, body + _pager(number, total), _sitenav(sections, shows, ('section', ident)))
        _write_pages(docs / SECTION_DIR / ident, paginate(by_section[ident]), render_section)
        written.append(f'{SECTION_DIR}/{ident}/index.html')
    records = sorted(archive.get('broadcasts', []), key=lambda r: r.get('created_at', 0), reverse=True)
    for ident, label, raw in shows:
        mine = [r for r in records if safe_id(r.get('show', '')) == ident]

        def render_show(number, items, total, ident=ident, label=label, mine=mine):
            body = (f"<p>{len(mine)} Sendungen, neueste zuerst.</p><ol class='page-list'>"
                    + ''.join(_broadcast_item(r, docs) for r in items) + '</ol>') if items else \
                "<p class='block-empty'>Zu dieser Sendung liegen noch keine Ausgaben vor.</p>"
            crumbs = [('Start', '../../index.html'), ('Archiv', '../../archive.html'), (label, page_name(number))]
            return _shell(label, site, crumbs, body + _pager(number, total), _sitenav(sections, shows, ('show', ident)))
        _write_pages(docs / SHOW_DIR / ident, paginate(mine), render_show)
        written.append(f'{SHOW_DIR}/{ident}/index.html')
    return written


def navigation_html(config):
    """Links to every Rubrik and Sendung page for the start page."""
    _, sections = sections_of(config)
    esc = html.escape
    items = ''.join(f"<li><a href='{SECTION_DIR}/{i}/index.html'>{esc(label)}</a></li>" for i, label, _ in sections)
    items += ''.join(f"<li><a href='{SHOW_DIR}/{i}/index.html'>{esc(label)}</a></li>" for i, label, _ in shows_of(config))
    return f"<nav class='sitenav' aria-label='Rubriken und Sendungen'><ul>{items}</ul></nav>"
