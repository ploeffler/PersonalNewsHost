#!/usr/bin/env python3
"""Conservative, extractive short news updates. No article scraping or invented facts."""
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import breaking_news  # noqa: E402


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, '', ''))


def select_updates(candidates, state, now, freshness_minutes=60, interval_minutes=15, breaking=None):
    """Candidates carry publisher publication times; modified dates never reset age.

    ``breaking`` are the settings from breaking_news.settings_from(); only
    breaking-news hits become updates, so runs without a hit produce no media.
    """
    breaking = breaking or breaking_news.settings_from({})
    cutoff = now - 86400
    updates = [u for u in state.get('updates', []) if cutoff < u['created_at'] <= now]
    seen = {k: v for k, v in state.get('seen', {}).items() if v['first_seen_at'] > now - 7 * 86400}
    new = []
    for c in sorted(candidates, key=lambda c: c['published_at'], reverse=True):
        url = canonical(c['url'])
        key = hashlib.sha256(url.encode()).hexdigest()[:24]
        fingerprint = hashlib.sha256((c['title'] + c['description']).encode()).hexdigest()
        previous = seen.get(key)
        seen[key] = {'first_seen_at': previous['first_seen_at'] if previous else now,
                     'fingerprint': fingerprint, 'published_at': c['published_at']}
        # Same article is never promoted again just for a changed timestamp or wording.
        if previous or not 0 <= now - c['published_at'] <= freshness_minutes * 60:
            continue
        if not c['description'] or not url.startswith(('https://', 'http://')):
            continue
        reason = breaking_news.assess(c, candidates, breaking, now, freshness_minutes * 60)
        if not reason:
            continue
        if any(SequenceMatcher(None, c['title'].casefold(), u['title'].casefold()).ratio() > .72
               for u in updates + new):
            continue
        new.append({**c, 'reason': reason, 'id': key, 'created_at': now, 'first_seen_at': now,
                    'expires_at': now + 86400, 'url': url})
    last = max((u['created_at'] for u in updates), default=0)
    today = breaking_news.local_day(now, breaking)
    # Stored updates are capped at five, so the daily count is kept separately.
    daily = {d: n for d, n in state.get('daily', {}).items() if d == today}
    used_today = max(daily.get(today, 0),
                     sum(1 for u in updates if breaking_news.local_day(u['created_at'], breaking) == today))
    if new and now - last >= interval_minutes * 60 and used_today < breaking['max_per_day']:
        updates.append(new[0])  # At most one update per run, newest first.
        used_today += 1
    return {'updates': sorted(updates, key=lambda u: u['created_at'], reverse=True)[:5], 'seen': seen,
            'daily': {today: used_today}}


def collect_candidates(news):
    original_timestamp = news.feed_timestamp
    def publication_timestamp(node):
        import copy
        node = copy.deepcopy(node)
        for changed in node.findall(news.ATOM + 'updated'):
            node.remove(changed)
        return original_timestamp(node)
    news.feed_timestamp = publication_timestamp
    candidates = []
    for feed in news.CONFIG.get('feeds', []):
        try:
            for title, description, url, _ in news.items_from_feed(feed):
                candidates.append({'title': title, 'description': description, 'url': url, 'feed': feed,
                                   'source': urlsplit(feed).hostname,
                                   'published_at': news.FEED_DATES.get(url, 0)})
        except Exception as exc:
            print(f'Feed unavailable: {feed}: {type(exc).__name__}')
    return candidates


def needs_media(result, docs):
    """True if a current update still lacks its clip; only then are speech/video tools needed."""
    return any(not (docs / 'short-update-video' / (u['id'] + '.mp4')).is_file() for u in result['updates'])


def publish_breaking(docs, updates, base, settings):
    """Breaking updates first in feed.xml and a banner slot on the start page."""
    feed = docs / 'feed.xml'
    if feed.is_file():
        feed.write_text(breaking_news.merge_into_feed(feed.read_text(encoding='utf-8'), updates, base), encoding='utf-8')
    home = docs / 'index.html'
    if home.is_file():
        page = home.read_text(encoding='utf-8')
        changed = breaking_news.inject_banner(page, settings['banner_hours'])
        if changed != page:
            home.write_text(changed, encoding='utf-8')


def main(argv=()):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', help='Only collect and select; store candidates in this file and report media need.')
    parser.add_argument('--from-plan', help='Reuse candidates and time from a --plan file.')
    args = parser.parse_args(list(argv))
    import generate as news
    docs = ROOT / 'docs'
    path = docs / 'short-updates.json'
    state_path = docs / 'short-update-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    settings = news.CONFIG.get('short_updates', {})
    breaking = breaking_news.settings_from(news.CONFIG)
    if args.from_plan:
        plan = json.loads(Path(args.from_plan).read_text(encoding='utf-8'))
        now, candidates = plan['now'], plan['candidates']
    else:
        now = dt.datetime.now(dt.timezone.utc).timestamp()
        candidates = collect_candidates(news) if settings.get('enabled', True) else []
    freshness = min(60, max(1, int(settings.get('freshness_minutes', 60))))
    interval = max(15, int(settings.get('interval_minutes', 15)))
    result = select_updates(candidates, state, now, freshness, interval, breaking)
    if args.plan:
        media = needs_media(result, docs)
        Path(args.plan).write_text(json.dumps({'now': now, 'candidates': candidates}, ensure_ascii=False), encoding='utf-8')
        print(f'Breaking-news updates: {len(result["updates"])}, media needed: {media}')
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
                output.write(f'media={"true" if media else "false"}\n')
        return result
    old_ids = {u['id'] for u in state.get('updates', [])}
    media_dir = docs / 'short-update-audio'
    media_dir.mkdir(exist_ok=True)
    video_dir = docs / 'short-update-video'
    video_dir.mkdir(exist_ok=True)
    for update in result['updates']:
        if update['id'] not in old_ids:
            update['text'] = news.edit_news(update['title'], update['description'], 'classic', 3, 900)
            # Keep complete sentences; clip long source prose without inventing a summary.
            if len(update['text'].split()) > 110:
                update['text'] = news.edit_news(update['title'], update['description'], 'brief', 1, 900)
            if len(update['text'].split()) <= 110:
                audio = media_dir / (update['id'] + '.wav')
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
                    render_short_update(update, docs / update['audio'], video, ROOT, news.CONFIG,
                                        breaking['max_clip_seconds'])
                except Exception as exc:
                    print(f'Short-update video unavailable: {type(exc).__name__}')
            if video.is_file():
                update['video'] = 'short-update-video/' + video.name
                update['video_bytes'] = video.stat().st_size
        update.pop('description', None)
    keep = {u.get('audio') for u in result['updates']}
    for audio in media_dir.glob('*.wav'):
        if 'short-update-audio/' + audio.name not in keep:
            audio.unlink()
    keep_videos = {u.get('video') for u in result['updates']}
    for video in video_dir.glob('*.mp4'):
        if 'short-update-video/' + video.name not in keep_videos:
            video.unlink()
    state_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    path.write_text(json.dumps({'updated_at': now, 'updates': result['updates']}, ensure_ascii=False, indent=2) + '\n')
    publish_breaking(docs, result['updates'], getattr(news, 'BASE', ''), breaking)
    return result


if __name__ == '__main__':
    main(sys.argv[1:])
