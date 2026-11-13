#!/usr/bin/env python3
"""Redaktionsübersicht: all current events of the 24-hour news store.

For every event group of the editorial pipeline the page lists the headline,
a two-sentence summary (verbatim sentences from the sources, nothing invented),
the publishers and whether the event is in the latest broadcast, was sent as a
breaking-news short update, was held back, or is not in the broadcast.
Writes docs/redaktion.json and docs/redaktion.html.
"""
import datetime as dt
import html
import importlib.util
import json
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
TZ = ZoneInfo('Europe/Vienna')
ISSUES = {'unsupported_headline': 'Überschrift nicht durch die Quelle gedeckt',
          'no_supported_prose': 'kein verwertbarer Text in der Quelle',
          'unverified_rendered_text': 'ungeprüfte Textänderung',
          'invalid_source_reference': 'ungültiger Quellenbezug',
          'conflicting_source_values': 'Quellen nennen abweichende Zahlen',
          'conflicting_source_wording': 'Quellen widersprechen sich in Verneinung oder Unsicherheit',
          'event_membership_not_supported': 'Zuordnung zum gemeinsamen Ereignis nicht belegt'}


def pipeline():
    spec = importlib.util.spec_from_file_location('editorial_pipeline', Path(__file__).resolve().parent / 'editorial_pipeline.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def read(path, default):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def canonical(url):
    parts = urlsplit(url or '')
    return urlunsplit((parts.scheme, parts.netloc.lower().removeprefix('www.'), parts.path.rstrip('/'), '', ''))


def clock(timestamp, with_day=False):
    moment = dt.datetime.fromtimestamp(timestamp, TZ)
    return moment.strftime('%d.%m. %H:%M' if with_day else '%H:%M')


def summary(p, group, members):
    """Two verbatim sentences: the verified draft, otherwise the opening of the newest report."""
    claims = [c['text'] for c in group['draft'].get('claims', [])][:2]
    if claims:
        return ' '.join(claims)
    for member in sorted(members, key=p.age, reverse=True):
        units = p.evidence_units(member)[:2]
        if units:
            return ' '.join(units)
    return ''


def build(store, broadcasts, short_state, pair_decisions, now, p=None):
    p = p or pipeline()
    report = p.prepare(store, now, pair_decisions=pair_decisions)
    latest = max(broadcasts.get('broadcasts', []), key=lambda b: b.get('created_at', 0), default=None)
    on_air = {canonical(s.get('url')) for s in (latest or {}).get('sources', []) if s.get('url')}
    announced = {}
    for event in short_state.get('events', []):
        for article_id in event.get('article_ids', []):
            announced[article_id] = event['created_at']
    events = []
    for group in report['groups']:
        members = [report['sources'][i] for i in group['member_ids']]
        publishers = list(dict.fromkeys(m['publisher'] for m in sorted(members, key=p.age)))
        in_broadcast = bool(on_air & {canonical(m.get('url')) for m in members})
        breaking = [announced[i] for i in group['member_ids'] if i in announced]
        held = group['verification']['status'] != 'approved'
        if in_broadcast:
            status, label = 'sendung', f"In der Sendung ({clock(latest['created_at'], True)})"
        elif held:
            reasons = [ISSUES.get(i, i) for i in group['verification'].get('issues', [])]
            status, label = 'zurueckgestellt', 'Zurückgestellt: ' + ('; '.join(reasons) or 'Prüfung nicht bestanden')
        else:
            status, label = 'nicht', 'Nicht in der Sendung'
        events.append({'id': group['id'], 'headline': group['draft']['headline'], 'summary': summary(p, group, members),
                       'publishers': publishers, 'reports': len(members), 'newest_at': max(map(p.age, members)),
                       'status': status, 'status_label': label,
                       'breaking_at': min(breaking) if breaking else None,
                       'links': [{'publisher': m['publisher'], 'title': m['title'], 'url': m.get('url', '')}
                                 for m in sorted(members, key=p.age)]})
    order = {'sendung': 0, 'nicht': 1, 'zurueckgestellt': 2}
    events.sort(key=lambda e: (order[e['status']], -min(len(e['publishers']), 3), -e['newest_at']))
    return {'generated_at': now, 'broadcast_at': latest['created_at'] if latest else None,
            'broadcast_title': latest.get('title') if latest else None, 'events': events}


def render(data):
    e = html.escape
    multi = [x for x in data['events'] if len(x['publishers']) > 1 or x['status'] == 'sendung']
    single = [x for x in data['events'] if x not in multi]

    def card(x):
        badge = f"<span class='badge {x['status']}'>{e(x['status_label'])}</span>"
        if x['breaking_at']:
            badge += f"<span class='badge eil'>Eilmeldung ({clock(x['breaking_at'])})</span>"
        links = ' · '.join(f"<a href='{e(l['url'])}' title='{e(l['title'])}'>{e(l['publisher'])}</a>" if l['url']
                           else e(l['publisher']) for l in x['links'])
        return (f"<article class='{x['status']}'><div class='badges'>{badge}</div>"
                f"<h2>{e(x['headline'])}</h2><p>{e(x['summary'])}</p>"
                f"<p class='meta'>{len(x['publishers'])} Medien · {x['reports']} Meldungen · zuletzt {clock(x['newest_at'])} · {links}</p></article>")

    counts = {s: sum(x['status'] == s for x in data['events']) for s in ('sendung', 'nicht', 'zurueckgestellt')}
    broadcast = (f"Letzte Sendung: {e(clock(data['broadcast_at'], True))} Uhr." if data['broadcast_at'] else 'Noch keine Sendung.')
    return ("<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Redaktionsübersicht · PersonalNewsHost</title><style>"
            "body{font:1rem/1.55 system-ui;background:#101c2c;color:#eff5ff;max-width:1000px;margin:2rem auto;padding:0 1.2rem}"
            "a{color:#8ed6ff}h1{font-size:1.7rem}h2{font-size:1.1rem;margin:.4rem 0}article{border:1px solid #344e68;border-radius:10px;"
            "padding:.9rem 1.1rem;margin:.8rem 0;background:#15263a}article.sendung{border-color:#6f8fd8}article.zurueckgestellt{opacity:.8}"
            ".badges{display:flex;gap:.4rem;flex-wrap:wrap}.badge{font-size:.75rem;padding:2px 8px;border-radius:5px;background:#2b3f55}"
            ".badge.sendung{background:#324773}.badge.zurueckgestellt{background:#633940}.badge.eil{background:#8a5a12}"
            ".meta{color:#adc2d9;font-size:.85rem;overflow-wrap:anywhere}summary{cursor:pointer;color:#9ed9ff;margin:1rem 0}"
            ".notice{color:#adc2d9}</style></head><body>"
            "<a href='index.html'>Zur Sendung</a> · <a href='short-updates.html'>Kurzupdates</a> · "
            "<a href='editorial-pipeline.html'>Quellenprüfung im Detail</a>"
            "<h1>Redaktionsübersicht</h1>"
            f"<p>Stand {e(clock(data['generated_at'], True))} Uhr · {broadcast} "
            f"{counts['sendung']} Ereignisse in der Sendung, {counts['nicht']} nicht in der Sendung, "
            f"{counts['zurueckgestellt']} zurückgestellt.</p>"
            "<p class='notice'>Alle Ereignisse der letzten 24 Stunden, gruppiert über mehrere Medien. Die Zusammenfassung besteht aus "
            "wörtlichen Sätzen der Quellen (keine eigene Formulierung, keine unabhängige Faktenprüfung). Wird alle 15 Minuten aktualisiert.</p>"
            f"<h2>Ereignisse mit mehreren Medien und Sendungsinhalte ({len(multi)})</h2>"
            + ''.join(card(x) for x in multi)
            + f"<details><summary>Einzelmeldungen ({len(single)})</summary>" + ''.join(card(x) for x in single) + "</details>"
            "</body></html>\n")


def main():
    store = read(DOCS / 'news-store.json', {'articles': [], 'feeds': []})
    p = pipeline()
    data = build(store, read(DOCS / 'broadcasts.json', {}), read(DOCS / 'short-update-state.json', {}),
                 p.load_pair_decisions(DOCS / 'event-pairs.json'), time.time(), p)
    (DOCS / 'redaktion.json').write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (DOCS / 'redaktion.html').write_text(render(data), encoding='utf-8')
    print(f"Redaktionsübersicht: {len(data['events'])} Ereignisse, "
          f"{sum(x['status'] == 'sendung' for x in data['events'])} in der Sendung")


if __name__ == '__main__':
    main()
