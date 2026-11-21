"""Configurable breaking-news detection, feed entries and site banner (T013).

Configuration lives in ``short_updates.breaking``::

    "breaking": {
      "keywords": ["eilmeldung", "evakuier*", ...],   # word starts with * = any ending
      "exclude_keywords": ["tier*"],
      "sources": ["https://example.org/eil.rss", "apa.at"],
      "min_sources": 1,
      "max_per_day": 6,
      "max_clip_seconds": 60,
      "banner_hours": 3
    }

A candidate is breaking news if it comes from a configured breaking source, or
if its title contains a keyword (and no excluded word) and at least
``min_sources`` different publishers report a similar title in the freshness
window. Nothing here produces media; callers render clips only for hits.
"""
import datetime as dt
import email.utils
import html
import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

DEFAULT_KEYWORDS = [
    'eilmeldung', 'breaking', '+++', 'soeben', 'beschlossen', 'entscheidet', 'zurückgetreten', 'rücktritt',
    'tritt zurück', 'gewinnt', 'bestätigt', 'abgesagt', 'gesperrt', 'evakuiert', 'angriff', 'earthquake',
    'resigns', 'announces', 'confirms', 'cancelled', 'evacuated']
DEFAULTS = {'keywords': DEFAULT_KEYWORDS, 'exclude_keywords': [], 'sources': [], 'min_sources': 1,
            'max_per_day': 6, 'max_clip_seconds': 60, 'banner_hours': 3, 'timezone': 'Europe/Vienna'}
CLIP_LIMIT = 60
FEED_GUID = 'eilmeldung:'
_WORDS = re.compile(r'[\wäöüß]{4,}', re.I)


def _strings(value):
    return [str(v).strip() for v in value if isinstance(v, str) and str(v).strip()] if isinstance(value, list) else []


def settings_from(config):
    """Validated settings; out-of-range numbers are clamped, never rejected."""
    short = config.get('short_updates', {}) if isinstance(config, dict) else {}
    raw = short.get('breaking', {}) if isinstance(short, dict) else {}
    raw = raw if isinstance(raw, dict) else {}
    s = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}

    def number(key, low, high):
        try:
            return min(high, max(low, int(s[key])))
        except (TypeError, ValueError):
            return DEFAULTS[key]
    keywords = _strings(s['keywords']) if 'keywords' in raw else DEFAULT_KEYWORDS
    return {'keywords': keywords, 'exclude_keywords': _strings(s['exclude_keywords']),
            'sources': _strings(s['sources']), 'min_sources': number('min_sources', 1, 5),
            'max_per_day': number('max_per_day', 0, 48),
            'max_clip_seconds': number('max_clip_seconds', 10, CLIP_LIMIT),
            'banner_hours': number('banner_hours', 0, 24), 'timezone': str(s['timezone'] or 'Europe/Vienna'),
            '_keyword_pattern': keyword_pattern(keywords),
            '_exclude_pattern': keyword_pattern(_strings(s['exclude_keywords']))}


def keyword_pattern(words):
    """Case-insensitive whole-word pattern; ``wort*`` allows any ending."""
    parts = []
    for word in words:
        stem, wildcard = (word[:-1], True) if word.endswith('*') else (word, False)
        if not stem:
            continue
        body = re.escape(stem) + (r'\w*' if wildcard else '')
        left = r'(?<!\w)' if stem[0].isalnum() else ''
        right = r'(?!\w)' if (wildcard or stem[-1].isalnum()) else ''
        parts.append(left + body + right)
    return re.compile('|'.join(parts), re.I) if parts else None


def publisher(candidate):
    host = (candidate.get('source') or urlsplit(candidate.get('url', '')).hostname or '').lower()
    return host[4:] if host.startswith('www.') else host


def from_breaking_source(candidate, settings):
    feed = candidate.get('feed', '')
    host = publisher(candidate)
    for source in settings['sources']:
        source = source.lower()
        if source.startswith(('https://', 'http://')):
            if feed and feed.rstrip('/') == source.rstrip('/'):
                return True
        elif host == source or host.endswith('.' + source):
            return True
    return False


def similar(a, b):
    a, b = a.casefold(), b.casefold()
    if SequenceMatcher(None, a, b).ratio() >= .6:
        return True
    wa, wb = set(_WORDS.findall(a)), set(_WORDS.findall(b))
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= .4


def assess(candidate, candidates, settings, now, freshness_seconds):
    """Return the reason (``Quelle``/``Stichwort``) if the candidate is breaking news, else None."""
    title = candidate.get('title', '')
    exclude = settings['_exclude_pattern']
    if exclude and exclude.search(title):
        return None
    if from_breaking_source(candidate, settings):
        return 'Quelle'
    keywords = settings['_keyword_pattern']
    if not keywords or not keywords.search(title):
        return None
    publishers = {publisher(candidate)}
    for other in candidates:
        if 0 <= now - other.get('published_at', 0) <= freshness_seconds and similar(title, other.get('title', '')):
            publishers.add(publisher(other))
    return 'Stichwort' if len(publishers) >= settings['min_sources'] else None


def local_day(timestamp, settings):
    return dt.datetime.fromtimestamp(timestamp, ZoneInfo(settings['timezone'])).date().isoformat()


def feed_items(updates, base):
    items = []
    for update in sorted(updates, key=lambda u: u['created_at'], reverse=True):
        enclosure = ''
        if update.get('video') and update.get('video_bytes'):
            enclosure = (f'<enclosure url="{html.escape(base + update["video"], quote=True)}" '
                         f'length="{int(update["video_bytes"])}" type="video/mp4"/>')
        items.append(
            '<item><title>' + html.escape('Eilmeldung: ' + update['title']) + '</title>'
            '<link>' + html.escape(base + 'short-updates.html#update-' + update['id']) + '</link>'
            '<guid isPermaLink="false">' + FEED_GUID + update['id'] + '</guid>'
            '<pubDate>' + email.utils.formatdate(update['created_at'], usegmt=True) + '</pubDate>'
            '<category>Eilmeldung</category>'
            '<description>' + html.escape(update.get('text') or update['title']) + '</description>'
            + enclosure + '</item>')
    return ''.join(items)


def merge_into_feed(feed, updates, base):
    """Replace previous breaking items in an RSS document and put current ones first."""
    feed = re.sub(r'<item>(?:(?!</item>).)*?<guid isPermaLink="false">' + FEED_GUID + r'.*?</item>', '', feed, flags=re.S)
    new = feed_items(updates, base)
    if not new:
        return feed
    position = feed.find('<item>')
    if position < 0:
        position = feed.find('</channel>')
    if position < 0:
        return feed
    return feed[:position] + new + feed[position:]


BANNER = ('<div id="breaking-banner" class="breaking-banner" role="alert" hidden '
          'data-hours="{hours}"></div>')
BANNER_SCRIPT = '<script src="breaking-banner.js" defer></script>'


def inject_banner(page, hours=3):
    """Placeholder at the top of the start page; breaking-banner.js fills it."""
    if 'id="breaking-banner"' in page or not hours:
        return page
    block = BANNER.format(hours=int(hours))
    for marker in ('<h1>', '<main'):
        if marker in page:
            page = page.replace(marker, block + marker, 1)
            break
    else:
        return page
    return page.replace('</html>', BANNER_SCRIPT + '</html>', 1) if BANNER_SCRIPT not in page else page
