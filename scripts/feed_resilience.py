#!/usr/bin/env python3
"""Resilient feed fetching: retry with backoff, last-good fallback, admin notice (T071).

* Only transient network problems are retried (timeouts, connection errors,
  HTTP 5xx and 429). Invalid URLs, 4xx and broken XML are not retried.
* The last successfully parsed body of every feed is kept in ``.cache/feeds/``.
  This directory is git-ignored and carried between workflow runs with
  ``actions/cache``; third-party feed content never lands in the public repo.
* A copy younger than ``reuse_seconds`` (default 300) is used without a new
  download, so the scripts of one workflow run fetch every feed only once.
* Health state is stored per feed under a hash key, so the private feed list
  never appears in logs, issues or the repository.
* ``--notify`` reports feeds that failed ``failure_threshold`` runs in a row:
  via Telegram to an admin chat (``TELEGRAM_BOT_TOKEN`` + ``TELEGRAM_ADMIN_CHAT_ID``)
  and/or as a GitHub issue (``GITHUB_TOKEN`` + ``GITHUB_REPOSITORY``, opt-in).
  At most once per feed and ``notify_interval_hours``.
"""
import argparse
import hashlib
import http.client
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULTS = {'attempts': 3, 'backoff_seconds': [2, 6], 'cache_max_age_hours': 48, 'reuse_seconds': 300,
            'failure_threshold': 3, 'notify_interval_hours': 24,
            'notify': {'telegram': True, 'github_issue': False}}
CACHE_DIR = Path('.cache') / 'feeds'
RUN_GAP_SECONDS = 300


def settings_from(config):
    raw = config.get('feed_resilience', {}) if isinstance(config, dict) else {}
    raw = raw if isinstance(raw, dict) else {}

    def number(key, low, high, cast=int):
        try:
            return min(high, max(low, cast(raw.get(key, DEFAULTS[key]))))
        except (TypeError, ValueError):
            return DEFAULTS[key]
    backoff = raw.get('backoff_seconds', DEFAULTS['backoff_seconds'])
    if not isinstance(backoff, list) or not all(isinstance(v, (int, float)) for v in backoff):
        backoff = DEFAULTS['backoff_seconds']
    notify = {**DEFAULTS['notify'], **(raw.get('notify') if isinstance(raw.get('notify'), dict) else {})}
    return {'attempts': number('attempts', 1, 5), 'backoff_seconds': [min(60.0, max(0.0, float(v))) for v in backoff],
            'cache_max_age_hours': number('cache_max_age_hours', 0, 24 * 14),
            'reuse_seconds': number('reuse_seconds', 0, 3600),
            'failure_threshold': number('failure_threshold', 1, 100),
            'notify_interval_hours': number('notify_interval_hours', 1, 24 * 7),
            'notify': {'telegram': bool(notify['telegram']), 'github_issue': bool(notify['github_issue'])}}


def is_transient(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code >= 500 or exc.code == 429
    return isinstance(exc, (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError,
                            http.client.IncompleteRead, http.client.RemoteDisconnected))


def fetch_with_retry(fetch, settings, sleep=None):
    """Call ``fetch()``; retry transient errors with the configured pauses."""
    attempts = settings['attempts']
    sleep = sleep or time.sleep
    for attempt in range(attempts):
        try:
            return fetch()
        except Exception as exc:
            if attempt + 1 >= attempts or not is_transient(exc):
                raise
            pauses = settings['backoff_seconds'] or [0]
            sleep(pauses[min(attempt, len(pauses) - 1)])


def feed_key(url):
    return hashlib.sha256(url.encode('utf-8')).hexdigest()[:20]


class FeedState:
    """Last good bodies and per-feed health under ``<root>/.cache/feeds``."""

    def __init__(self, root):
        self.dir = Path(root) / CACHE_DIR
        self.health_path = self.dir / 'health.json'

    def health(self):
        try:
            data = json.loads(self.health_path.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_health(self, data):
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.health_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        tmp.replace(self.health_path)

    def record(self, url, ok, now, error=''):
        data = self.health()
        entry = data.get(feed_key(url), {})
        if ok:
            entry.update(failures=0, last_success_at=now, first_failure_at=None, last_failure_at=None, last_error='')
        else:
            # Several scripts read the same feed in one workflow run; count runs, not calls.
            last = entry.get('last_failure_at')
            if last is None or now - float(last) >= RUN_GAP_SECONDS:
                entry['failures'] = int(entry.get('failures', 0)) + 1
            if entry.get('first_failure_at') is None:
                entry['first_failure_at'] = now
            entry['last_failure_at'] = now
            entry['last_error'] = error
        entry['host'] = urllib.parse.urlsplit(url).hostname or ''
        data[feed_key(url)] = entry
        self.save_health(data)
        return entry

    def store(self, url, body):
        self.dir.mkdir(parents=True, exist_ok=True)
        target = self.dir / (feed_key(url) + '.xml')
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(body)
        tmp.replace(target)

    def cached(self, url, max_age_seconds, now):
        path = self.dir / (feed_key(url) + '.xml')
        try:
            if now - path.stat().st_mtime <= max_age_seconds:
                return path.read_bytes()
        except OSError:
            pass
        return None


def load_feed(url, fetch, parse, config, root, now=None, sleep=None):
    """Fetch and parse one feed; on lasting failure fall back to the last good body.

    Returns the parsed document. Raises the original error only if neither
    a fresh nor a cached body is usable, so the caller can skip this feed.
    """
    settings = settings_from(config)
    state = FeedState(root)
    now = time.time() if now is None else now
    # Several scripts in one workflow run read the same feeds; a copy fetched
    # moments ago is reused instead of downloading again (T070, saves minutes).
    fresh = state.cached(url, settings['reuse_seconds'], now) if settings['reuse_seconds'] else None
    if fresh is not None:
        try:
            return parse(fresh)
        except Exception:
            pass
    try:
        body = fetch_with_retry(fetch, settings, sleep)
        document = parse(body)
    except Exception as exc:
        state.record(url, False, now, type(exc).__name__)
        cached = state.cached(url, settings['cache_max_age_hours'] * 3600, now)
        if cached is not None:
            try:
                document = parse(cached)
                print(f'Feed unavailable ({type(exc).__name__}); using last valid copy')
                return document
            except Exception:
                pass
        raise
    state.store(url, body)
    state.record(url, True, now)
    return document


def due_notices(root, config, now=None):
    """Health entries of persistently failing feeds that should be reported now."""
    settings = settings_from(config)
    now = time.time() if now is None else now
    feeds = list(dict.fromkeys(config.get('feeds', []))) if isinstance(config, dict) else []
    positions = {feed_key(url): index + 1 for index, url in enumerate(feeds)}
    due = []
    for key, entry in FeedState(root).health().items():
        if key not in positions or int(entry.get('failures', 0)) < settings['failure_threshold']:
            continue
        notified = entry.get('notified_at')
        if notified is not None and now - float(notified) < settings['notify_interval_hours'] * 3600:
            continue
        due.append({'key': key, 'position': positions[key], **entry})
    return sorted(due, key=lambda e: e['position'])


def _post(url, payload, headers):
    request = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json', **headers}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        return 200 <= response.status < 300


def _since(entry, now):
    first = entry.get('first_failure_at')
    hours = (now - float(now if first is None else first)) / 3600
    return f'{hours:.1f} h'


def notify(root, config, env, now=None, post=_post):
    """Send notices for due feeds; returns the channels used. No secrets, no feed URLs in issues."""
    settings = settings_from(config)
    now = time.time() if now is None else now
    due = due_notices(root, config, now)
    if not due:
        return []
    sent = []
    title = str(config.get('title', 'PersonalNewsHost'))
    token, chat = env.get('TELEGRAM_BOT_TOKEN', ''), env.get('TELEGRAM_ADMIN_CHAT_ID', '')
    if settings['notify']['telegram'] and token and chat:
        lines = [f'⚠ {title}: RSS-Feeds dauerhaft gestört'] + [
            f"• Feed Nr. {e['position']} ({e.get('host') or 'unbekannt'}): {e['failures']} Fehlversuche in Folge, "
            f"seit {_since(e, now)}, zuletzt {e.get('last_error') or 'Fehler'}" for e in due]
        lines.append('Die Sendung läuft mit den übrigen Feeds bzw. der letzten gültigen Kopie weiter.')
        try:
            if post(f'https://api.telegram.org/bot{token}/sendMessage',
                    {'chat_id': chat, 'text': '\n'.join(lines), 'disable_web_page_preview': True}, {}):
                sent.append('telegram')
        except Exception as exc:
            print(f'Telegram admin notice failed: {type(exc).__name__}')
    repo, gh_token = env.get('GITHUB_REPOSITORY', ''), env.get('GITHUB_TOKEN', '')
    if settings['notify']['github_issue'] and repo and gh_token:
        # Public issue: feed position and error type only, never the feed URL or host.
        body = '\n'.join(['Folgende Feeds aus der Konfiguration sind dauerhaft nicht abrufbar:', ''] + [
            f"- Feed Nr. {e['position']}: {e['failures']} Fehlversuche in Folge seit {_since(e, now)}, "
            f"zuletzt `{e.get('last_error') or 'Fehler'}`" for e in due] + [
            '', 'Die Sendung läuft mit den übrigen Feeds weiter. Automatisch erzeugt von `scripts/feed_resilience.py`.'])
        try:
            if post(f'https://api.github.com/repos/{repo}/issues',
                    {'title': f'RSS-Feeds dauerhaft gestört ({len(due)})', 'body': body, 'labels': ['feed-health']},
                    {'Authorization': f'Bearer {gh_token}', 'Accept': 'application/vnd.github+json'}):
                sent.append('github_issue')
        except Exception as exc:
            print(f'GitHub issue notice failed: {type(exc).__name__}')
    if sent:
        state = FeedState(root)
        health = state.health()
        for entry in due:
            health.setdefault(entry['key'], {})['notified_at'] = now
        state.save_health(health)
    else:
        print(f'{len(due)} persistently failing feed(s); no notification channel configured')
    return sent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--notify', action='store_true', help='Report persistently failing feeds.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    config_path = args.root / 'config.json'
    if not config_path.is_file():
        config_path = args.root / 'config.example.json'
    try:
        config = json.loads(config_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        print(f'No readable configuration ({type(exc).__name__}); nothing to report')
        return 0
    if args.notify:
        channels = notify(args.root, config, os.environ)
        print('Feed notices sent: ' + (', '.join(channels) if channels else 'none'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
