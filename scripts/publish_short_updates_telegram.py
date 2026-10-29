#!/usr/bin/env python3
"""Two-phase Telegram delivery: persist attempt IDs before contacting Telegram."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def destination(config, env):
    telegram = config.get('telegram', {})
    if (not telegram.get('enabled', False)
            or not config.get('short_updates', {}).get('telegram_enabled', True)
            or not config.get('short_updates', {}).get('enabled', True)):
        return None
    target = telegram.get('target', 'default')
    if target not in ('default', 'secondary'):
        raise ValueError('Invalid telegram.target')
    token = env.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat = env.get('TELEGRAM_CHAT_ID' if target == 'default' else 'TELEGRAM_CHAT_ID_SECONDARY', '').strip()
    if not token or not chat:
        raise ValueError('Telegram credentials missing for configured destination')
    key = target + ':' + hashlib.sha256(chat.encode()).hexdigest()[:16]
    return token, chat, key


def clip(text, limit):
    """Telegram limits count UTF-16 units; never split a surrogate pair."""
    return str(text).encode('utf-16-le')[:limit * 2].decode('utf-16-le', errors='ignore')


def message(update, base):
    stamp = dt.datetime.fromtimestamp(update['created_at'], dt.timezone.utc).strftime('%d.%m.%Y %H:%M UTC')
    body = clip(update.get('text') or update['title'], 2400)
    url = str(update.get('url', ''))
    source = clip(update.get('source', ''), 100)
    footer = '\n\nAlle Kurzupdates: ' + base.rstrip('/') + '/short-updates.html'
    if url.startswith(('https://', 'http://')) and len(url.encode('utf-16-le')) <= 1600:
        footer = '\n\nQuelle: ' + source + '\n' + url + footer
    return clip('Kurzupdate · ' + stamp + '\n\n' + body + footer, 4096)


def prepare(root, queue, env, now):
    # Never leave an earlier queue eligible for sending after a disabled/no-op run.
    queue.parent.mkdir(parents=True, exist_ok=True)
    queue.write_text(json.dumps({'destination': None, 'updates': []}), encoding='utf-8')
    config = read_json(root / 'config.json', {})
    updates = read_json(root / 'docs/short-updates.json', {}).get('updates', [])
    fresh = [u for u in updates if 0 <= now - u['created_at'] < 3600
             and re.fullmatch('[a-f0-9]{24}', str(u.get('id', '')))]
    if not fresh:
        print('No recent short updates to send.')
        return
    dest = destination(config, env)
    if dest is None:
        print('Short-update Telegram delivery disabled.')
        return
    ledger_path = root / '.state/short-update-telegram.json'
    ledger = read_json(ledger_path, {'attempts': {}})
    attempts = {k: v for k, v in ledger['attempts'].items() if v > now - 7 * 86400}
    pending = []
    for u in sorted(fresh, key=lambda u: u['created_at'])[-5:]:
        key = dest[2] + '/' + u['id']
        if key not in attempts:
            pending.append(u)
            attempts[key] = now
    if pending:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps({'attempts': attempts}, indent=2) + '\n', encoding='utf-8')
    queue.write_text(json.dumps({'destination': dest[2], 'updates': pending}, ensure_ascii=False), encoding='utf-8')
    print(f'Telegram short updates reserved: {len(pending)}')


def deliver(root, queue, env, now):
    queued = read_json(queue, {'updates': []})
    if not queued['updates']:
        print('No new Telegram short updates.')
        return
    dest = destination(read_json(root / 'config.json', {}), env)
    if dest is None or dest[2] != queued['destination']:
        raise ValueError('Telegram destination changed after reservation')
    base = env.get('PUBLIC_BASE_URL', 'https://ploeffler.github.io/PersonalNewsHost/')
    if not base.startswith('https://') or len(base) > 300:
        raise ValueError('Invalid public site URL')
    attempts = read_json(root / '.state/short-update-telegram.json', {'attempts': {}})['attempts']
    # Consume the local queue before network I/O, too: a repeated --send never resends it.
    queue.write_text(json.dumps({'destination': None, 'updates': []}), encoding='utf-8')
    failures = 0
    for update in queued['updates']:
        if not 0 <= now - update['created_at'] < 3600:
            continue
        if dest[2] + '/' + update['id'] not in attempts:
            raise ValueError('Short update was not reserved')
        payload = {'chat_id': dest[1], 'text': message(update, base),
                   'link_preview_options': json.dumps({'is_disabled': True})}
        request = urllib.request.Request('https://api.telegram.org/bot' + dest[0] + '/sendMessage',
                                         data=urllib.parse.urlencode(payload).encode(), method='POST')
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)
            if not result.get('ok'):
                raise RuntimeError('Telegram rejected short update')
            print('Telegram short update delivered: ' + update['id'])
        except Exception as exc:
            # Exception strings may contain the credential-bearing URL. Never log them.
            print('Telegram delivery failed (' + type(exc).__name__ + '); no automatic retry to avoid duplicates.', file=sys.stderr)
            failures += 1
    if failures:
        raise RuntimeError('One or more Telegram deliveries failed; check Actions run')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--send', action='store_true')
    parser.add_argument('--queue', type=Path, required=True)
    args = parser.parse_args()
    try:
        (prepare if args.prepare else deliver)(ROOT, args.queue, os.environ, time.time())
    except Exception as exc:
        print('Telegram short-update step failed: ' + type(exc).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
