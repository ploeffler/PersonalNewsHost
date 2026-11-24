"""Start page in editorial layout (T021).

The page keeps the existing player and playlist (Aufmacher), the breaking-news
bar (T013) and the 24-hour news list. This module adds static blocks that work
without JavaScript:

* Rubriken: the newest headlines of the last 24 hours per broadcast section
  (``editorial.broadcast_sections``: feed assignments, then headline keywords)
* Neueste Beiträge: the newest headlines across all sources

The blocks are rendered from ``docs/news-store.json`` and replaced between
fixed markers, so every RSS run (collect_news.py) refreshes them in place.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

START, END = '<!-- pnh:blocks:start -->', '<!-- pnh:blocks:end -->'
WINDOW_SECONDS = 24 * 3600
PER_SECTION = 4
LATEST = 6
THEME_SCRIPT = '<script src="theme.js"></script>'


def _section_of(article, settings):
    sections = settings.get('sections', [])
    valid = {s.get('id') for s in sections}
    for feed in article.get('feed_urls', []):
        assigned = settings.get('feed_sections', {}).get(feed)
        if assigned in valid:
            return assigned
    title = str(article.get('title', '')).casefold()
    for section in sections:
        if any(re.search(r'(?<!\w)' + re.escape(word.casefold()) + r'(?!\w)', title)
               for word in section.get('keywords', []) if word):
            return section['id']
    default = settings.get('default', 'general')
    return default if default in valid else 'general'


def _host(url):
    host = (urlsplit(url).hostname or '').lower()
    return host[4:] if host.startswith('www.') else host


def _safe(url):
    return url if str(url).startswith(('https://', 'http://')) else ''


def recent_articles(store, now, window=WINDOW_SECONDS):
    items = []
    for article in store.get('articles', []):
        published = article.get('published_at') or article.get('first_seen_at') or 0
        if article.get('title') and _safe(article.get('url', '')) and 0 <= now - published <= window:
            items.append((published, article))
    return [a for _, a in sorted(items, key=lambda x: x[0], reverse=True)]


def _article_links(manifest):
    return {a.get('title'): a.get('path') for a in (manifest or {}).get('articles', []) if a.get('path')}


def _item(article, published, links, zone):
    local = dt.datetime.fromtimestamp(published, dt.timezone.utc).astimezone(zone)
    page = links.get(article['title'])
    href, extra = (page, '') if page else (article['url'], " rel='noopener noreferrer'")
    title = html.escape(article['title'])
    return (f"<li><a href='{html.escape(href, quote=True)}'{extra}>{title}</a>"
            f"<span class='block-meta'>{html.escape(_host(article['url']))} · "
            f"<time datetime='{local.isoformat()}'>{local.strftime('%H:%M')}</time></span></li>")


def render_blocks(store, config, manifest=None, now=None, zone='Europe/Vienna'):
    """HTML for the Rubriken and Neueste Beiträge blocks, between markers."""
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    zone = ZoneInfo(zone)
    settings = (config.get('editorial', {}) or {}).get('broadcast_sections', {}) or {}
    sections = settings.get('sections') or [{'id': 'general', 'label': 'Allgemein'}]
    labels = {s['id']: s.get('label', s['id']) for s in sections}
    order = [s['id'] for s in sections]
    articles = recent_articles(store, now)
    links = _article_links(manifest)
    grouped = {}
    for article in articles:
        grouped.setdefault(_section_of(article, settings), []).append(article)
    stamp = lambda a: a.get('published_at') or a.get('first_seen_at') or 0  # noqa: E731
    blocks = []
    for ident in order + sorted(set(grouped) - set(order)):
        items = grouped.get(ident, [])[:PER_SECTION]
        if not items:
            continue
        heading = f'rubrik-{re.sub(r"[^a-z0-9-]", "-", ident.lower())}'
        blocks.append(f"<section class='ressort' aria-labelledby='{heading}'><h3 id='{heading}'>"
                      f"{html.escape(labels.get(ident, ident))}</h3><ul>"
                      + ''.join(_item(a, stamp(a), links, zone) for a in items) + '</ul></section>')
    if not blocks:
        blocks.append("<p class='block-empty'>In den letzten 24 Stunden sind keine Meldungen eingegangen.</p>")
    latest = ''.join(_item(a, stamp(a), links, zone) for a in articles[:LATEST]) or \
        "<li class='block-empty'>Noch keine Beiträge.</li>"
    updated = dt.datetime.fromtimestamp(now, dt.timezone.utc).astimezone(zone)
    try:
        from scripts.section_pages import navigation_html
    except ModuleNotFoundError:
        from section_pages import navigation_html
    return (START + "<div class='homepage-blocks'>"
            "<section id='ressorts' class='ressorts' aria-labelledby='ressorts-heading'>"
            "<h2 id='ressorts-heading'>Rubriken</h2><div class='ressort-grid'>" + ''.join(blocks) + '</div></section>'
            "<section id='latest-posts' class='latest-posts' aria-labelledby='latest-heading'>"
            "<h2 id='latest-heading'>Neueste Beiträge</h2><ol class='latest-list'>" + latest + '</ol>'
            f"<p class='block-meta'>Stand <time datetime='{updated.isoformat()}'>{updated.strftime('%d.%m.%Y, %H:%M')}</time>"
            " · <a href='#news-overview'>Alle Nachrichten der letzten 24 Stunden</a>"
            " · <a href='search.html'>Suche</a></p></section></div>"
            + navigation_html(config) + END)


THEME_TOGGLE = ("<button type='button' id='theme-toggle' class='theme-toggle' aria-pressed='false'>"
                "Dunkles Design</button>")


def place_blocks(page, blocks):
    """Insert or replace the blocks; idempotent. Also links site.css and the theme switch."""
    if START in page and END in page:
        page = page[:page.index(START)] + blocks + page[page.index(END) + len(END):]
    elif '<section id="news-overview"' in page:
        page = page.replace('<section id="news-overview"', blocks + '<section id="news-overview"', 1)
    elif '</main>' in page:
        page = page.replace('</main>', '</main>' + blocks, 1)
    else:
        page = page.replace('</html>', blocks + '</html>', 1)
    if 'href="site.css"' not in page:
        # Loaded last so its variables and layout win over older inline rules.
        page = page.replace('</style>', '</style><link rel="stylesheet" href="site.css">', 1) if '</style>' in page \
            else page.replace('<title>', '<link rel="stylesheet" href="site.css"><title>', 1)
    if 'id="theme-toggle"' not in page and "id='theme-toggle'" not in page and '<h1>' in page:
        page = page.replace('<h1>', THEME_TOGGLE + '<h1>', 1)
    if THEME_SCRIPT not in page:
        page = page.replace('</html>', THEME_SCRIPT + '</html>', 1)
    return page


def update_homepage(docs, config, now=None):
    """Refresh the static blocks of docs/index.html from docs/news-store.json."""
    docs = Path(docs)
    home = docs / 'index.html'
    if not home.is_file():
        return False

    def read(name, default):
        try:
            return json.loads((docs / name).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return default
    try:
        from scripts import breaking_news
    except ModuleNotFoundError:
        import breaking_news
    page = home.read_text(encoding='utf-8')
    updated = place_blocks(page, render_blocks(read('news-store.json', {}), config,
                                               read('articles.json', {}), now))
    # Breaking-news bar at the top (T013); no-op if already present.
    updated = breaking_news.inject_banner(updated, breaking_news.settings_from(config)['banner_hours'])
    if updated != page:
        home.write_text(updated, encoding='utf-8')
    # Rubriken- und Sendungsseiten (T022) folgen jedem RSS-Lauf und jeder Sendung.
    try:
        from scripts.section_pages import build_section_pages
    except ModuleNotFoundError:
        from section_pages import build_section_pages
    build_section_pages(docs, config, store=read('news-store.json', {}), archive=read('archive.json', {}),
                        manifest=read('articles.json', {}), now=now)
    try:
        from scripts.search_index import write_index
    except ModuleNotFoundError:
        from search_index import write_index
    write_index(docs, config, store=read('news-store.json', {}), archive=read('archive.json', {}),
                manifest=read('articles.json', {}), now=now or 0)
    return True


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Refresh the static start-page blocks of a docs folder.')
    parser.add_argument('--refresh', type=Path, required=True, help='docs folder with index.html and news-store.json')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'config.json')
    parser.add_argument('--now', type=float, help='Reference time (Unix seconds); default: news-store updated_at or now')
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding='utf-8')) if args.config.is_file() else {}
    now = args.now
    if now is None:
        try:
            now = json.loads((args.refresh / 'news-store.json').read_text(encoding='utf-8')).get('updated_at')
        except (OSError, ValueError):
            now = None
    print('updated' if update_homepage(args.refresh, config, now) else 'no index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
