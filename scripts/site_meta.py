"""Sitemap, robots.txt, Open-Graph-/Twitter-Card-Metadaten und schema.org-Daten (T032).

* ``sitemap.xml``: Startseite, Archiv, Suche sowie alle Artikel-, Rubriken- und
  Sendungsseiten (inklusive Folgeseiten der Paginierung).
* ``robots.txt``: erlaubt alles und verweist auf die Sitemap.
* Metadaten: ein Block zwischen festen Markern im ``<head>`` jeder dieser Seiten
  (Open Graph, Twitter Card, kanonische URL, JSON-LD ``NewsArticle`` für
  Artikelseiten, ``VideoObject`` für die aktuelle Sendung auf der Startseite,
  ``CollectionPage`` für Rubriken und Sendungen). Der Block wird bei jedem Lauf
  ersetzt; Wiederholung ist ein No-op.
* Basis-Adresse: ``site.base_url`` in der Konfiguration, sonst ``PNH_BASE_URL``,
  sonst die Standardadresse der Projektseite.
"""
import datetime as dt
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

DEFAULT_BASE = 'https://ploeffler.github.io/PersonalNewsHost/'
START, END = '<!-- pnh:meta:start -->', '<!-- pnh:meta:end -->'
SECTIONS = ('rubrik', 'sendung', 'artikel')
ROOT_PAGES = ('index.html', 'archive.html', 'search.html', 'ueber-diese-sendung.html')
MAX_URLS = 50000
STAMP = re.compile(r'(\d{8})T(\d{6})Z')


def base_url(config, env=None):
    env = os.environ if env is None else env
    raw = str(((config.get('site') or {}).get('base_url')) or env.get('PNH_BASE_URL') or DEFAULT_BASE).strip()
    if not re.match(r'https?://[^\s<>"\']+$', raw):
        raw = DEFAULT_BASE
    return raw if raw.endswith('/') else raw + '/'


def page_files(docs):
    docs = Path(docs)
    files = [name for name in ROOT_PAGES if (docs / name).is_file()]
    for folder in SECTIONS:
        files += sorted(p.relative_to(docs).as_posix() for p in (docs / folder).rglob('*.html')) if (docs / folder).is_dir() else []
    return files[:MAX_URLS]


def page_url(base, relative):
    if relative == 'index.html':
        return base
    return base + quote(relative, safe='/')


def build_sitemap(docs, base):
    docs = Path(docs)
    rows = []
    for relative in page_files(docs):
        modified = dt.datetime.fromtimestamp((docs / relative).stat().st_mtime, dt.timezone.utc).date().isoformat()
        rows.append(f"  <url><loc>{html.escape(page_url(base, relative))}</loc><lastmod>{modified}</lastmod></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + '\n'.join(rows) + '\n</urlset>\n')


def build_robots(base):
    return f'User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n'


def _text(fragment):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def _head_info(page):
    title = re.search(r'<title>(.*?)</title>', page, re.S)
    description = re.search(r"<meta name=['\"]description['\"] content=['\"]([^'\"]*)['\"]", page)
    if description:
        text = html.unescape(description.group(1))
    else:
        body = re.search(r'<p[^>]*>(.*?)</p>', page.split('<h1', 1)[-1], re.S)
        text = _text(body.group(1)) if body else ''
    when = re.search(r"<time datetime=['\"]([^'\"]+)['\"]", page)
    return (_text(title.group(1)) if title else ''), text[:200], (when.group(1) if when else '')


def _json_ld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def meta_block(relative, page, base, site, latest_video=None):
    title, description, when = _head_info(page)
    url = page_url(base, relative)
    kind = 'article' if relative.startswith('artikel/') else 'website'
    esc = lambda v: html.escape(str(v), quote=True)  # noqa: E731
    tags = [f'<link rel="canonical" href="{esc(url)}">',
            f'<meta property="og:site_name" content="{esc(site)}">', f'<meta property="og:type" content="{kind}">',
            f'<meta property="og:title" content="{esc(title)}">', f'<meta property="og:url" content="{esc(url)}">',
            '<meta property="og:locale" content="de_AT">',
            '<meta name="twitter:card" content="summary">', f'<meta name="twitter:title" content="{esc(title)}">']
    if description:
        tags += [f'<meta property="og:description" content="{esc(description)}">',
                 f'<meta name="twitter:description" content="{esc(description)}">']
    publisher = {'@type': 'Organization', 'name': site}
    data = []
    if kind == 'article':
        stamp = STAMP.search(relative)
        published = when or (dt.datetime.strptime(stamp.group(1) + stamp.group(2), '%Y%m%d%H%M%S').replace(
            tzinfo=dt.timezone.utc).isoformat() if stamp else '')
        article = {'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': title.split(' – ')[0][:110],
                   'mainEntityOfPage': url, 'publisher': publisher, 'inLanguage': 'de'}
        if description:
            article['description'] = description
        if published:
            article['datePublished'] = published
        data.append(article)
    elif relative.startswith(('rubrik/', 'sendung/')):
        data.append({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title, 'url': url,
                     'isPartOf': {'@type': 'WebSite', 'name': site, 'url': base}, 'inLanguage': 'de'})
    elif relative == 'index.html':
        data.append({'@context': 'https://schema.org', '@type': 'WebSite', 'name': site, 'url': base, 'inLanguage': 'de'})
        if latest_video:
            data.append(latest_video)
    return START + ''.join(tags) + ''.join(_json_ld(d) for d in data) + END


def place_meta(page, block):
    if START in page and END in page:
        return page[:page.index(START)] + block + page[page.index(END) + len(END):]
    return page.replace('</head>', block + '</head>', 1) if '</head>' in page else page


def latest_video_object(docs, base, site):
    try:
        entries = json.loads((Path(docs) / 'broadcasts.json').read_text(encoding='utf-8')).get('broadcasts', [])
    except (OSError, ValueError):
        return None
    entries = [e for e in entries if e.get('video') and e.get('created_at')]
    if not entries:
        return None
    entry = max(entries, key=lambda e: e['created_at'])
    return {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': str(entry.get('title', site)),
            'description': str(entry.get('title', site)),
            'uploadDate': dt.datetime.fromtimestamp(entry['created_at'], dt.timezone.utc).isoformat(),
            'contentUrl': base + quote(str(entry['video']), safe='/'), 'inLanguage': 'de'}


def _write(path, text):
    if not path.is_file() or path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8')


def update_site_meta(docs, config, env=None):
    docs = Path(docs)
    base = base_url(config, env)
    site = str(config.get('title', 'PersonalNewsHost'))
    video = latest_video_object(docs, base, site)
    for relative in page_files(docs):
        path = docs / relative
        page = path.read_text(encoding='utf-8')
        updated = place_meta(page, meta_block(relative, page, base, site, video))
        if updated != page:
            path.write_text(updated, encoding='utf-8')
    _write(docs / 'sitemap.xml', build_sitemap(docs, base))
    _write(docs / 'robots.txt', build_robots(base))
    return base
