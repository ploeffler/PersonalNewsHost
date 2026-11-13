#!/usr/bin/env python3
"""Local language model as yes/no judge for borderline event pairs.

The rules in editorial_pipeline keep two reports apart unless their headlines
clearly match. Pairs that share two or more headline word stems but are kept
apart ("borderline") are asked to a small local model (llama.cpp server with
Qwen3-4B-Instruct) once, in both orders: "Same concrete event? ja/nein";
only a consistent "ja" counts. Answers are stored in
docs/event-pairs.json and used by the pipeline for the broadcast and for
breaking-news detection. The model never writes broadcast text.

--plan   count pending pairs (no model needed); writes pending=N to GITHUB_OUTPUT
--judge  ask the running llama.cpp server, within a time budget
"""
import argparse
import importlib.util
import itertools
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = ROOT / 'docs' / 'event-pairs.json'
DEFAULTS = {'enabled': True, 'max_pairs_per_run': 40, 'time_budget_seconds': 150,
            'server_url': 'http://127.0.0.1:8080'}
MODEL = 'Qwen3-4B-Instruct-2507-Q4_K_M'
SYSTEM = ('Du bist Nachrichtenredakteur. Entscheide, ob zwei Meldungen dieselbe Nachricht über denselben konkreten '
          'Vorfall melden. Antworte „ja“ nur, wenn beide im Kern dasselbe berichten (zum Beispiel beide den Rücktritt, '
          'beide denselben Unfall, beide dieselbe Entscheidung). Antworte „nein“, wenn eine Meldung eine Folge, '
          'Reaktion, Analyse, Vorgeschichte, ein Hintergrund oder eine andere Entwicklung zum selben Thema ist – zum '
          'Beispiel Rücktritt und spätere Vorladung vor einen Ausschuss, Rücktritt und Vorschlag eines Nachfolgers, '
          'Vorfall und spätere Ehrung, Ereignis und Kommentar dazu. Im Zweifel „nein“. '
          'Antworte nur mit einem Wort: ja oder nein.')


def pipeline():
    spec = importlib.util.spec_from_file_location('editorial_pipeline', Path(__file__).resolve().parent / 'editorial_pipeline.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def read(path, default):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def settings(config):
    raw = config.get('editorial', {}).get('pipeline', {}).get('llm_pairs', {}) if isinstance(config, dict) else {}
    s = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    s['enabled'] = bool(s['enabled'])
    s['max_pairs_per_run'] = min(200, max(0, int(s['max_pairs_per_run'])))
    s['time_budget_seconds'] = min(600, max(10, int(s['time_budget_seconds'])))
    return s


def pending_pairs(store, decided, now, p):
    """Borderline pairs of different publishers from the last 24 h, newest first."""
    articles = [a for a in store.get('articles', []) if a.get('id') and a.get('title')
                and a.get('content_kind') != 'non_news' and now - 86400 < p.age(a) <= now]
    feeds = store.get('feeds', [])
    for a in articles:
        a['_publisher'] = p.publisher(a, feeds)
    pairs = []
    for a, b in itertools.combinations(articles, 2):
        if a['_publisher'] == b['_publisher'] or p.pair_key(a, b) in decided:
            continue
        if p.borderline(a, b) and p.places_compatible(a, b):
            pairs.append((max(p.age(a), p.age(b)), a, b))
    return [(a, b) for _, a, b in sorted(pairs, key=lambda x: -x[0])]


def brief(p, article):
    return article['title'] + ' – ' + ' '.join(p.evidence_units(article)[:2])


def ask(url, p, a, b, timeout=60):
    body = {'messages': [{'role': 'system', 'content': SYSTEM},
                         {'role': 'user', 'content': f'Meldung A: {brief(p, a)}\n\nMeldung B: {brief(p, b)}\n\nDasselbe konkrete Ereignis?'}],
            'temperature': 0, 'max_tokens': 4, 'cache_prompt': True,
            'chat_template_kwargs': {'enable_thinking': False}}
    request = urllib.request.Request(url.rstrip('/') + '/v1/chat/completions', json.dumps(body).encode(),
                                     {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        answer = json.load(response)['choices'][0]['message']['content']
    match = re.search(r'\b(ja|nein)\b', answer, re.I)
    return None if not match else match[1].lower() == 'ja'


def prune(data, store):
    alive = {a['id'] for a in store.get('articles', []) if a.get('id')}
    data['pairs'] = {k: v for k, v in data.get('pairs', {}).items() if set(k.split('|')) <= alive}
    return data


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--judge', action='store_true')
    args = parser.parse_args(argv)
    p = pipeline()
    cfg = settings(read(ROOT / 'config.json', {}))
    store = read(ROOT / 'docs' / 'news-store.json', {'articles': [], 'feeds': []})
    now = time.time()
    data = prune(read(PAIRS, {'version': 1, 'model': MODEL, 'pairs': {}}), store)
    pending = pending_pairs(store, data['pairs'], now, p) if cfg['enabled'] else []
    if args.plan:
        count = min(len(pending), cfg['max_pairs_per_run'])
        print(f'Grenzfall-Paare offen: {len(pending)} (dieser Lauf prüft höchstens {count})'
              if cfg['enabled'] else 'Sprachmodell-Prüfung abgeschaltet (editorial.pipeline.llm_pairs.enabled)')
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                out.write(f'pending={count}\n')
    if args.judge:
        start, asked, same = time.monotonic(), 0, 0
        for a, b in pending[:cfg['max_pairs_per_run']]:
            if time.monotonic() - start > cfg['time_budget_seconds']:
                print('Zeitbudget erreicht; restliche Paare im nächsten Lauf.')
                break
            try:
                # Ask in both orders; only a consistent "ja" counts.
                first, second = ask(cfg['server_url'], p, a, b), ask(cfg['server_url'], p, b, a)
            except OSError as exc:
                print(f'Sprachmodell nicht erreichbar ({type(exc).__name__}); es gelten nur die Regeln.')
                break
            if first is None or second is None:
                continue
            verdict = first and second
            asked += 1; same += verdict
            data['pairs'][p.pair_key(a, b)] = {'same': verdict, 'decided_at': round(now)}
            print(f"{'ja  ' if verdict else 'nein'} · {a['title']} ⟷ {b['title']}")
        print(f'{asked} Paare geprüft in {time.monotonic() - start:.0f} s, davon {same} als dasselbe Ereignis erkannt.')
    data['model'] = MODEL
    PAIRS.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
