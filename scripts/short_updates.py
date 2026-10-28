#!/usr/bin/env python3
"""Conservative, extractive short news updates. No article scraping or invented facts."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = re.compile(r'\b(eilmeldung|breaking|soeben|beschlossen|entscheidet|zurückgetreten|rücktritt|tritt zurück|gewinnt|bestätigt|abgesagt|gesperrt|evakuiert|angriff|earthquake|resigns|announces|confirms|cancelled|evacuated)\b', re.I)


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, '', ''))


def select_updates(candidates, state, now, freshness_minutes=60, interval_minutes=15):
    """Candidates carry publisher publication times; modified dates never reset age."""
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
        if not SIGNALS.search(c['title']) or not c['description'] or not url.startswith(('https://', 'http://')):
            continue
        if any(SequenceMatcher(None, c['title'].casefold(), u['title'].casefold()).ratio() > .72
               for u in updates + new):
            continue
        new.append({**c, 'id': key, 'created_at': now, 'first_seen_at': now,
                    'expires_at': now + 86400, 'url': url})
    last = max((u['created_at'] for u in updates), default=0)
    if new and now - last >= interval_minutes * 60:
        updates.append(new[0])  # At most one update per run, newest first.
    return {'updates': sorted(updates, key=lambda u: u['created_at'], reverse=True)[:5], 'seen': seen}


def main():
    import generate as news
    original_timestamp = news.feed_timestamp
    def publication_timestamp(node):
        import copy
        node = copy.deepcopy(node)
        for changed in node.findall(news.ATOM + 'updated'):
            node.remove(changed)
        return original_timestamp(node)
    news.feed_timestamp = publication_timestamp
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    path = ROOT / 'docs' / 'short-updates.json'
    state_path = ROOT / 'docs' / 'short-update-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    settings = news.CONFIG.get('short_updates', {})
    candidates = []
    if settings.get('enabled', True):
        for feed in news.CONFIG.get('feeds', []):
            try:
                for title, description, url, _ in news.items_from_feed(feed):
                    candidates.append({'title': title, 'description': description, 'url': url,
                                       'source': urlsplit(feed).hostname,
                                       'published_at': news.FEED_DATES.get(url, 0)})
            except Exception as exc:
                print(f'Feed unavailable: {feed}: {type(exc).__name__}')
    result = select_updates(candidates, state, now,
                            min(60, max(1, int(settings.get('freshness_minutes', 60)))),
                            max(15, int(settings.get('interval_minutes', 15))))
    old_ids = {u['id'] for u in state.get('updates', [])}
    media_dir = ROOT / 'docs' / 'short-update-audio'
    media_dir.mkdir(exist_ok=True)
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
        update.pop('description', None)
    keep = {u.get('audio') for u in result['updates']}
    for audio in media_dir.glob('*.wav'):
        if 'short-update-audio/' + audio.name not in keep:
            audio.unlink()
    state_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    path.write_text(json.dumps({'updated_at': now, 'updates': result['updates']}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
