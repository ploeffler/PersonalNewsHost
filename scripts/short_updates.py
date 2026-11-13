#!/usr/bin/env python3
"""Short updates for breaking news only.

The RSS run stores all feed items first (collect_news.py). This script then
looks at *events* – groups of reports about the same occurrence from the
editorial pipeline – and decides whether one of them is breaking news:

* explicitly marked (Eilmeldung, Breaking, +++), or from a configured breaking feed;
* serious (deaths, explosion, attack, collapse, …; not animals) or a change in a
  top office, reported by at least two publishers within the window;
* Austrian relevance plus an urgent development (threat, warning, flood, …),
  reported by at least two publishers within the window.

Texts are the verified, extractive multi-source drafts of the pipeline – nothing
is invented. Media (speech, video) are only produced when an update needs them,
so a run without breaking news needs no speech or video tools.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = Path(__file__).resolve().parent / 'editorial_pipeline.py'
MAX_MEDIA_ATTEMPTS = 2

MARKED = re.compile(r'\b(eilmeldung|eil|breaking)\b|\+\+\+', re.I)
# "Tote" only as noun (capitalised) so "400 toten Schweinen" does not count as deaths.
DEATHS = re.compile(r'\bTote[nr]?\b|\bTodesopfer\b|\bgetötet\b|\bist tot\b|\btot aufgefunden\b|\btot gefunden\b|\btot in\b')
SERIOUS = re.compile(r'\b(explosion\w*|explodiert|anschlag|attentat|terror\w*|erdbeben|tsunami|evakuiert|evakuierung|'
                     r'geiselnahme|absturz|abgestürzt|stürzt ab|amoklauf|schüsse|erschossen|großbrand|einsturz|'
                     r'eingestürzt|krieg|waffenruhe|killed|dead|earthquake|explosion|attack|shooting)\b', re.I)
ANIMALS = re.compile(r'\b(schwein\w*|rind\w*|kühe|kuh|tier\w*|fisch\w*|vögel|vogel\w*|hühner|hund\w*|katze\w*|'
                     r'tauben?|wölfe?|wolf|bär\w*|hahn|pferd\w*)\b', re.I)
TOP_OFFICE = re.compile(r'\b(kanzler\w*|präsident\w*|minister\w*|regierung\w*|ceo|chef\w*|papst|bürgermeister\w*|'
                        r'landeshauptm\w*|president|prime minister)\b', re.I)
OFFICE_CHANGE = re.compile(r'\b(rücktritt|tritt zurück|zurückgetreten|entlassen|abgesetzt|gestorben|verstorben|'
                           r'festgenommen|resigns|resigned|fired|dies|died)\b', re.I)
AUSTRIA = re.compile(r'\b(österreich\w*|austria\w*|wien\w*|nö|oö|niederösterreich\w*|oberösterreich\w*|steiermark|'
                     r'steirisch\w*|kärnten|kärntner\w*|tirol\w*|salzburg\w*|vorarlberg\w*|burgenland\w*|graz\w*|'
                     r'linz\w*|innsbruck\w*|klagenfurt\w*|villach\w*|st\. pölten|bregenz\w*|eisenstadt\w*|wels|'
                     r'leoben|bundesheer|nationalrat|bundesregierung|bundeskanzler\w*|bundespräsident\w*|öbb|'
                     r'asfinag|övp|spö|fpö|neos)\b', re.I)
URGENT = re.compile(r'\b(droht|drohung|warnt|warnung|alarm|notstand|neuwahl\w*|regierungskrise|koalitionsbruch|'
                    r'misstrauen\w*|ausweis\w*|vergeltung|unwetter\w*|hochwasser|überflutung\w*|lawine\w*|'
                    r'stromausfall|blackout|streik\w*|großeinsatz|vermisst\w*|festgenommen|razzia)\b', re.I)

DEFAULTS = {'enabled': True, 'freshness_minutes': 60, 'window_minutes': 180, 'min_publishers': 2,
            'max_per_day': 6, 'interval_minutes': 15, 'austria_rule': True, 'breaking_feeds': [],
            'timezone': 'Europe/Vienna'}


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, '', ''))


def load_pipeline():
    spec = importlib.util.spec_from_file_location('editorial_pipeline', PIPELINE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def settings_from(config):
    raw = config.get('short_updates', {}) if isinstance(config, dict) else {}
    s = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    s['freshness_minutes'] = min(120, max(5, int(s['freshness_minutes'])))
    s['window_minutes'] = min(720, max(30, int(s['window_minutes'])))
    s['min_publishers'] = min(5, max(1, int(s['min_publishers'])))
    s['max_per_day'] = min(48, max(0, int(s['max_per_day'])))
    s['interval_minutes'] = max(15, int(s['interval_minutes']))
    s['breaking_feeds'] = [str(f) for f in s['breaking_feeds'] if isinstance(f, str)]
    return s


def serious(title):
    return bool((DEATHS.search(title) or SERIOUS.search(title)) and not ANIMALS.search(title))


def assess(members, settings, now, pipeline):
    """Return (reason, publisher count) if the event is breaking news, else (None, n)."""
    times = [pipeline.age(m) for m in members]
    window = settings['window_minutes'] * 60
    publishers = {m['publisher'] for m, t in zip(members, times) if now - window < t <= now}
    titles = [m['title'] for m in members]
    if now - max(times) > settings['freshness_minutes'] * 60:
        return None, len(publishers)          # no fresh report in this event
    breaking_feeds = set(settings['breaking_feeds'])
    if any(MARKED.search(t) for t in titles) or any(set(m.get('feed_urls', [])) & breaking_feeds for m in members):
        return 'Kennzeichnung', len(publishers)
    if now - min(times) > window or len(publishers) < settings['min_publishers']:
        return None, len(publishers)          # old story, or not yet confirmed by a second publisher
    if any(serious(t) for t in titles):
        return 'Schwere', len(publishers)
    if any(TOP_OFFICE.search(t) and OFFICE_CHANGE.search(t) for t in titles):
        return 'Spitzenamt', len(publishers)
    if settings['austria_rule']:
        context = ' '.join(m['title'] + ' ' + (pipeline.sentence_units(m.get('text', ''))[:1] or [''])[0] for m in members)
        if AUSTRIA.search(context) and any(URGENT.search(t) for t in titles):
            return 'Österreich', len(publishers)
    return None, len(publishers)


def local_day(timestamp, settings):
    return dt.datetime.fromtimestamp(timestamp, ZoneInfo(settings['timezone'])).date().isoformat()


def update_text(draft):
    text = draft['text'].strip()
    if len(text.split()) > 110:  # keep complete, verified sentences only
        lines = text.split('\n')
        text = '\n'.join([lines[0]] + [c['text'] for c in draft['claims'][:1]] + [lines[-1]])
    return text


def select_breaking(store, state, now, settings, pipeline=None):
    pipeline = pipeline or load_pipeline()
    updates = [u for u in state.get('updates', []) if now - 86400 < u['created_at'] <= now]
    events = [e for e in state.get('events', []) if now - 3 * 86400 < e['created_at'] <= now]
    covered = {i for e in events for i in e['article_ids']}
    decisions = pipeline.load_pair_decisions(ROOT / 'docs' / 'event-pairs.json')
    report = pipeline.prepare(store, now, pair_decisions=decisions) if settings['enabled'] else {'groups': [], 'sources': {}}
    candidates = []
    for group in report['groups']:
        if group['verification']['status'] != 'approved' or not group['draft']['claims']:
            continue
        if covered & set(group['member_ids']):
            continue                          # already announced this event
        members = [report['sources'][i] for i in group['member_ids']]
        reason, count = assess(members, settings, now, pipeline)
        if not reason:
            continue
        headline = group['draft']['headline']
        if any(SequenceMatcher(None, headline.casefold(), u['title'].casefold()).ratio() > .72 for u in updates):
            continue
        candidates.append((reason == 'Kennzeichnung', count, group['newest_at'], group, members, reason))
    last = max((u['created_at'] for u in updates), default=0)
    today = sum(local_day(e['created_at'], settings) == local_day(now, settings) for e in events)
    if candidates and now - last >= settings['interval_minutes'] * 60 and today < settings['max_per_day']:
        _, count, _, group, members, reason = max(candidates, key=lambda c: c[:3])
        primary = report['sources'][group['draft']['headline_source_id']]
        url = canonical(primary.get('url', ''))
        update = {'id': hashlib.sha256((url or group['id']).encode()).hexdigest()[:24],
                  'title': group['draft']['headline'], 'text': update_text(group['draft']),
                  'url': url, 'source': primary['publisher'],
                  'sources': sorted({m['publisher'] for m in members}),
                  'published_at': min(pipeline.age(m) for m in members),
                  'created_at': now, 'expires_at': now + 86400, 'reason': reason, 'publishers': count}
        updates.append(update)
        events.append({'created_at': now, 'article_ids': group['member_ids'], 'reason': reason,
                       'title': update['title']})
    updates = sorted(updates, key=lambda u: u['created_at'], reverse=True)[:5]
    return {'updates': updates, 'events': events}


def needs_media(updates):
    return [u for u in updates if not u.get('video') and u.get('media_attempts', 0) < MAX_MEDIA_ATTEMPTS]


def produce_media(updates, media_dir, video_dir):
    import generate as news
    for update in needs_media(updates):
        audio = media_dir / (update['id'] + '.wav')
        if not update.get('audio') and len(update['text'].split()) <= 120:
            try:
                news.synthesize(update['text'], audio)
                update['audio'] = 'short-update-audio/' + audio.name
            except Exception as exc:
                print(f'Speech unavailable: {type(exc).__name__}')
        if update.get('audio') and re.fullmatch(r'short-update-audio/[a-f0-9]{24}\.wav', update['audio']):
            video = video_dir / (update['id'] + '.mp4')
            if not video.is_file():
                try:
                    try:
                        from scripts.short_update_video import render_short_update
                    except ModuleNotFoundError:
                        from short_update_video import render_short_update
                    render_short_update(update, ROOT / 'docs' / update['audio'], video, ROOT, news.CONFIG)
                except Exception as exc:
                    print(f'Short-update video unavailable: {type(exc).__name__}')
            if video.is_file():
                update['video'] = 'short-update-video/' + video.name
        if not update.get('video'):
            update['media_attempts'] = update.get('media_attempts', 0) + 1


def read(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def main(argv=None):
    args = argparse.ArgumentParser()
    args.add_argument('--detect', action='store_true', help='only decide; no speech or video tools needed')
    args.add_argument('--media', action='store_true', help='only produce missing speech and video')
    args = args.parse_args(argv if argv is not None else [])
    both = not args.detect and not args.media
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    docs = ROOT / 'docs'
    path, state_path = docs / 'short-updates.json', docs / 'short-update-state.json'
    media_dir, video_dir = docs / 'short-update-audio', docs / 'short-update-video'
    media_dir.mkdir(parents=True, exist_ok=True); video_dir.mkdir(parents=True, exist_ok=True)
    state = read(state_path, {})
    if args.detect or both:
        settings = settings_from(read(ROOT / 'config.json', {}))
        store = read(docs / 'news-store.json', {'articles': [], 'feeds': []})
        state = select_breaking(store, state, now, settings)
        new = [u for u in state['updates'] if u['created_at'] == now]
        for u in new:
            print(f"Eilmeldung erkannt ({u['reason']}, {u['publishers']} Medien): {u['title']}")
        if not new:
            print('Keine Eilmeldung in diesem Lauf.')
    if args.media or both:
        produce_media(state['updates'], media_dir, video_dir)
    keep_audio = {u.get('audio') for u in state['updates']}
    for audio in media_dir.glob('*.wav'):
        if 'short-update-audio/' + audio.name not in keep_audio:
            audio.unlink()
    keep_video = {u.get('video') for u in state['updates']}
    for video in video_dir.glob('*.mp4'):
        if 'short-update-video/' + video.name not in keep_video:
            video.unlink()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    path.write_text(json.dumps({'updated_at': now, 'updates': state['updates']}, ensure_ascii=False, indent=2) + '\n')
    if args.detect and os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write(f"media_needed={'true' if needs_media(state['updates']) else 'false'}\n")


if __name__ == '__main__':
    main(sys.argv[1:])
