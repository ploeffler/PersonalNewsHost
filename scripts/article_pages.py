"""Static article pages per bulletin story (T020).

Pages are plain HTML files for GitHub Pages: no server, no external
resources and no trackers. Each page carries only the short editorial
summary that was also spoken in the bulletin, never full source texts.
"""
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

ARTICLE_DIR = 'artikel'
SUMMARY_LIMIT = 600
STAMP = re.compile(r'\d{8}T\d{6}Z')
_TRANSLIT = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'})


def broadcast_stamp(published_at):
    """Same identifier as scripts/broadcast_archive.py uses for the video."""
    return dt.datetime.fromtimestamp(published_at, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def slugify(text, limit=60):
    slug = re.sub(r'[^a-z0-9]+', '-', str(text).lower().translate(_TRANSLIT)).strip('-')
    return slug[:limit].rstrip('-') or 'meldung'


def article_path(stamp, index, title):
    return f'{ARTICLE_DIR}/{stamp}/{index + 1:02d}-{slugify(title)}.html'


def clean_summary(text, limit=SUMMARY_LIMIT):
    """Spoken story text without the section announcement, cut at a sentence end."""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if lines and lines[0].startswith('Nun zum Bereich '):
        lines = lines[1:]
    summary = ' '.join(lines)
    if len(summary) <= limit:
        return summary
    cut = summary[:limit]
    end = max(cut.rfind('. '), cut.rfind('! '), cut.rfind('? '))
    return cut[:end + 1] if end > 0 else cut.rsplit(' ', 1)[0] + ' …'


def _clock(seconds):
    seconds = max(0, int(seconds))
    return f'{seconds // 60}:{seconds % 60:02d}'


def _safe_url(url):
    return url if str(url).startswith(('https://', 'http://')) else ''


STYLE = (
    ':root{color-scheme:light dark;--bg:#f6f8fb;--fg:#13202f;--muted:#4b5b6e;--accent:#0b6fa4;--card:#fff}'
    '@media(prefers-color-scheme:dark){:root{--bg:#13243a;--fg:#f2f6fa;--muted:#b9c7d6;--accent:#8ed6ff;--card:#1b304b}}'
    'body{margin:0;background:var(--bg);color:var(--fg);font:1.05rem/1.6 system-ui,sans-serif}'
    'main{max-width:52rem;margin:0 auto;padding:1rem 1.2rem 3rem}'
    'a{color:var(--accent)}h1{font-size:clamp(1.5rem,4vw,2.2rem);line-height:1.25;margin:.4rem 0 .8rem}'
    '.meta{color:var(--muted);font-size:.95rem}.rubrik{text-transform:uppercase;letter-spacing:.05em;font-weight:600;color:var(--accent)}'
    'video{width:100%;height:auto;border-radius:.4rem;background:#000}'
    'section{background:var(--card);border-radius:.5rem;padding:.8rem 1.1rem;margin:1.2rem 0}'
    'nav{font-size:.95rem}.hinweis{color:var(--muted);font-size:.9rem}'
)


def render_article(story, stamp, published_at, base_title, zone='Europe/Vienna'):
    """Return the HTML for one story dict."""
    local = dt.datetime.fromtimestamp(published_at, dt.timezone.utc).astimezone(ZoneInfo(zone))
    shown = local.strftime('%d.%m.%Y, %H:%M Uhr')
    start = max(0.0, float(story.get('start') or 0))
    video = f'../../broadcasts/{stamp}.mp4#t={start:.1f}'
    subtitles = f'../../broadcasts/{stamp}.vtt'
    esc = html.escape
    rubrik = ' · '.join(x for x in (story.get('section_label'), story.get('category')) if x)
    sources = []
    for source in story.get('sources', []):
        url = _safe_url(source.get('url', ''))
        label = esc(source.get('title') or url or 'Quelle')
        host = re.sub(r'^https?://(www\.)?([^/]+).*$', r'\2', url) if url else ''
        if url:
            sources.append(f"<li><a rel='noopener noreferrer' href='{esc(url, quote=True)}'>{label}</a>"
                           f" <span class='meta'>({esc(host)})</span></li>")
        else:
            sources.append(f'<li>{label}</li>')
    original = _safe_url((story.get('sources') or [{}])[0].get('url', ''))
    original_link = (f"<p><a rel='noopener noreferrer' href='{esc(original, quote=True)}'>Zum Originalartikel</a></p>"
                     if original else '')
    summary = clean_summary(story.get('summary', ''))
    return ''.join([
        "<!doctype html><html lang='de'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<meta name='referrer' content='no-referrer'>",
        f"<title>{esc(story['title'])} – {esc(base_title)}</title>",
        f"<meta name='description' content='{esc(summary[:160], quote=True)}'>",
        f'<style>{STYLE}</style></head><body><main>',
        "<nav><a href='../../index.html'>← Zur aktuellen Sendung</a></nav><article>",
        f"<p class='rubrik'>{esc(rubrik)}</p>" if rubrik else '',
        f"<h1>{esc(story['title'])}</h1>",
        f"<p class='meta'>Sendung vom <time datetime='{local.isoformat()}'>{esc(shown)}</time></p>",
        f'<p>{esc(summary)}</p>' if summary else '',
        f"<p class='meta bildnachweis'>{esc(story['image_credit'])}</p>" if story.get('image_credit') else '',
        original_link,
        "<section aria-label='Video'>",
        f"<video controls preload='metadata' src='{esc(video, quote=True)}'>",
        f"<track kind='subtitles' src='{esc(subtitles, quote=True)}' srclang='de' label='Deutsch' default></video>",
        f"<p><a href='{esc(video, quote=True)}'>Diese Meldung im Video ab {_clock(start)} ansehen</a></p></section>",
        f"<section aria-label='Quellen'><h2>Quellen</h2><ul>{''.join(sources)}</ul></section>",
        "<p class='hinweis'>Automatisch aus RSS-Meldungen erstellt, mit KI-Unterstützung. "
        'Die Zusammenfassung ist kurz gehalten; Details stehen in den verlinkten Originalquellen. '
        'Inhalte wurden nicht unabhängig überprüft.</p>',
        "</article><nav aria-label='Rechtliches'><a href='../../datenschutz.html'>Datenschutz</a> · "
        "<a href='../../impressum.html'>Impressum</a></nav></main></body></html>\n",
    ])


def _kept_stamps(docs):
    manifest = Path(docs) / 'broadcasts.json'
    try:
        entries = json.loads(manifest.read_text(encoding='utf-8')).get('broadcasts', [])
    except (OSError, ValueError):
        return set()
    return {e.get('id') for e in entries if isinstance(e, dict)}


def build_article_pages(docs, stories, published_at, base_title, enabled=True):
    """Write one page per story and the manifest ``articles.json``.

    Article folders of bulletins that are no longer in ``broadcasts.json``
    are removed, so pages never point at a deleted archive video.
    Returns the relative page paths in story order.
    """
    docs = Path(docs)
    if not enabled:
        return []
    stamp = broadcast_stamp(published_at)
    target = docs / ARTICLE_DIR / stamp
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    paths, manifest = [], []
    for index, story in enumerate(stories):
        relative = article_path(stamp, index, story['title'])
        (docs / relative).write_text(render_article(story, stamp, published_at, base_title), encoding='utf-8')
        paths.append(relative)
        manifest.append({'title': story['title'], 'path': relative,
                         'category': story.get('category'), 'section': story.get('section'),
                         'video': f'broadcasts/{stamp}.mp4', 'start': round(float(story.get('start') or 0), 3),
                         'sources': [s.get('url') for s in story.get('sources', []) if _safe_url(s.get('url', ''))]})
    keep = _kept_stamps(docs) | {stamp}
    for folder in (docs / ARTICLE_DIR).iterdir():
        if folder.is_dir() and STAMP.fullmatch(folder.name) and folder.name not in keep:
            shutil.rmtree(folder)
    (docs / 'articles.json').write_text(
        json.dumps({'broadcast': stamp, 'published_at': published_at, 'articles': manifest},
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return paths


def link_articles_on_homepage(page, titles, paths):
    """Static list of this bulletin's article pages on the start page.

    Inserted before the JavaScript news overview, or before the closing tag,
    so the links also work without JavaScript.
    """
    if not paths:
        return page
    items = ''.join(f"<li><a href='{html.escape(path, quote=True)}'>{html.escape(title)}</a></li>"
                    for title, path in zip(titles, paths))
    block = ('<section id="bulletin-articles" aria-labelledby="bulletin-articles-heading">'
             '<h2 id="bulletin-articles-heading">Meldungen dieser Sendung</h2>'
             f'<ol>{items}</ol></section>\n')
    marker = '<section id="news-overview"'
    if marker in page:
        return page.replace(marker, block + marker, 1)
    return page.replace('</html>', block + '</html>', 1)
