#!/usr/bin/env python3
"""Experiment (nicht produktiv): lokales Sprachmodell (llama.cpp-Server) fuer
Gruppierung und Zusammenfassung. Misst Zeiten und prueft Belege.

Erwartet einen laufenden llama-server auf LLM_URL (Standard http://127.0.0.1:8080).
"""
import importlib.util, itertools, json, os, random, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get('LLM_URL', 'http://127.0.0.1:8080') + '/v1/chat/completions'
OUT = []
CALLS = []


def say(*lines):
    for line in lines:
        print(line, flush=True); OUT.append(line)


def pipeline():
    spec = importlib.util.spec_from_file_location('ep', ROOT / 'scripts/editorial_pipeline.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def chat(system, user, schema=None, max_tokens=200):
    body = {'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
            'temperature': 0, 'max_tokens': max_tokens, 'cache_prompt': True,
            'chat_template_kwargs': {'enable_thinking': False}}
    if schema:
        body['response_format'] = {'type': 'json_schema', 'json_schema': {'name': 'a', 'schema': schema}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    dt = time.perf_counter() - t0
    usage = data.get('usage', {})
    timings = data.get('timings', {})
    CALLS.append({'s': dt, 'in': usage.get('prompt_tokens', 0), 'out': usage.get('completion_tokens', 0),
                  'pp': timings.get('prompt_per_second'), 'tg': timings.get('predicted_per_second')})
    text = data['choices'][0]['message']['content'].strip()
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()
    if not schema:
        return text, dt
    try:
        return json.loads(text), dt
    except json.JSONDecodeError:
        m = re.search(r'\b(ja|nein)\b', text, re.I)
        print('Rohantwort:', repr(text[:200]), data['choices'][0].get('finish_reason'), flush=True)
        return {'gleich': m[1].lower() if m else '?'}, dt


def brief(p, a, n=2):
    units = p.evidence_units(a)[:n]
    return a['title'] + ' – ' + ' '.join(units)


SYS_SAME = ('Du bist Nachrichtenredakteur. Entscheide, ob zwei Meldungen über dasselbe konkrete Ereignis '
            'berichten (gleicher Vorfall, gleiche Entscheidung, gleiche Aussage). Meldungen zum selben großen '
            'Thema, aber über verschiedene Teilereignisse oder Folgeentwicklungen, sind NICHT dasselbe Ereignis.')
SCHEMA_SAME = {'type': 'object', 'properties': {'gleich': {'type': 'string', 'enum': ['ja', 'nein']}}, 'required': ['gleich']}

SYS_SUM = ('Du bist Nachrichtenredakteur für eine deutschsprachige Radiosendung. Fasse die Meldungen zu EINEM '
           'Ereignis in 2 bis 3 kurzen, sachlichen Sätzen zusammen, geeignet zum Vorlesen. Verwende ausschließlich '
           'Fakten, Zahlen und Namen, die in den Quellen stehen. Keine Wertungen, keine Vermutungen, keine '
           'Quellenangabe, keine Überschrift. Gib nur den Text aus.')


def support_check(text, sources_text):
    """Every number and every capitalised word (not sentence-initial) must occur in the sources."""
    src = sources_text.casefold()
    missing = []
    for num in re.findall(r'\d+(?:[.,]\d+)*', text):
        if num not in sources_text and num.replace('.', '') not in sources_text.replace('.', ''):
            missing.append(num)
    for sent in re.split(r'(?<=[.!?])\s+', text):
        words = re.findall(r'[A-ZÄÖÜ][\wäöüß-]{2,}', sent)[1:]
        for w in words:
            stem = w.casefold()[:max(4, len(w) - 3)]
            if stem not in src:
                missing.append(w)
    return sorted(set(missing))


def main():
    p = pipeline()
    store = json.loads((ROOT / 'docs/news-store.json').read_text(encoding='utf-8'))
    now = store['updated_at']
    arts = {a['id']: a for a in store['articles'] if a.get('id') and a.get('title')}
    say('# Testlauf lokales Sprachmodell (llama.cpp)', '',
        f"Modell: `{os.environ.get('LLM_MODEL', '?')}` · Datenstand {time.strftime('%d.%m.%Y %H:%M UTC', time.gmtime(now))} "
        f"· {len(arts)} Artikel · Ladezeiten: {os.environ.get('LLM_TIMES', '?')}", '')

    # Warm-up (erste Antwort enthaelt Modell-Initialisierung)
    _, warm = chat('Antworte mit ok.', 'ok?', max_tokens=3)
    say(f'Erste Antwort (Aufwärmen): {warm:.1f}s', '')

    # --- 1. Gruppierung: knifflige Paare -----------------------------------
    report = p.prepare(store, now)
    publ = lambda a: p.publisher(a, [])
    ids = list(arts)
    rule_pos, near = [], []
    for x, y in itertools.combinations(ids, 2):
        a, b = arts[x], arts[y]
        if publ(a) == publ(b):
            continue
        shared = len(p.stems(a['title']) & p.stems(b['title']))
        if p.same_event(a, b):
            rule_pos.append((a, b))
        elif shared >= 2:
            near.append((a, b))
    random.seed(7)
    sample = [('Regel: gleich', a, b) for a, b in random.sample(rule_pos, min(12, len(rule_pos)))]
    sample += [('Regel: verschieden', a, b) for a, b in random.sample(near, min(28, len(near)))]
    say(f'## 1. Gruppierung: {len(sample)} Paare (12 die die Regeln zusammenlegen, 28 Grenzfälle mit ≥2 gemeinsamen Wortstämmen, die die Regeln trennen)', '')
    t0 = time.perf_counter(); rows = []; agree = 0
    for label, a, b in sample:
        ans, dt = chat(SYS_SAME + ' Antworte nur mit einem Wort: ja oder nein.',
                       f'Meldung A: {brief(p, a)}\n\nMeldung B: {brief(p, b)}\n\nDasselbe konkrete Ereignis?', None, 4)
        m = re.search(r'\b(ja|nein)\b', ans, re.I)
        llm = m[1].lower() if m else '?(' + ans[:20] + ')'
        agree += (llm == 'ja') == label.endswith('gleich')
        rows.append(f"- {dt:4.1f}s · {label} · **LLM: {llm}** · {a['title']} ⟷ {b['title']}")
    t_group = time.perf_counter() - t0
    say(f'Gesamt {t_group:.0f}s, Ø {t_group / len(sample):.1f}s pro Paar · Übereinstimmung mit den Regeln: {agree}/{len(sample)}', '', *rows, '')

    # Hochrechnung fuer den inkrementellen Betrieb
    per_15 = len(arts) / 96
    say(f'Hochrechnung: ca. {per_15:.1f} neue Artikel pro 15 Minuten; bei 3 Kandidatenprüfungen je Artikel '
        f'≈ {per_15 * 3 * t_group / len(sample):.0f}s Modellzeit pro Kurzupdate-Lauf.', '')

    # --- 2. Zusammenfassung der 5 ausgewaehlten Meldungen -------------------
    selected = p.select(report, 5)
    say('## 2. Zusammenfassung der 5 ausgewählten Meldungen', '')
    t0 = time.perf_counter(); held = 0
    for g in selected:
        members = [report['sources'][sid] for sid in g['member_ids']]
        src = '\n\n'.join(f"Quelle {i + 1} ({m['publisher']}): {m['title']}. " + ' '.join(p.evidence_units(m)[:4])
                          for i, m in enumerate(members))
        text, dt = chat(SYS_SUM, src, max_tokens=180)
        missing = support_check(text, '\n'.join(m['title'] + ' ' + m.get('text', '') for m in members))
        held += bool(missing)
        say(f"### {g['draft']['headline']} ({len(members)} Quelle(n), {dt:.1f}s)", '',
            '**Heute (wörtliche Sätze):** ' + g['draft']['text'].split('\n', 1)[1].rsplit('\n', 1)[0], '',
            '**Sprachmodell:** ' + text, '',
            ('**Belegprüfung:** nicht belegt → ' + ', '.join(missing) + ' → Rückfall auf heutigen Text') if missing
            else '**Belegprüfung:** alle Zahlen und Namen in den Quellen gefunden ✓', '')
    t_sum = time.perf_counter() - t0
    say(f'Zusammenfassung gesamt {t_sum:.0f}s (Ø {t_sum / max(1, len(selected)):.1f}s pro Meldung), Belegprüfung durchgefallen: {held}/{len(selected)}', '')

    # --- 3. Rechenleistung --------------------------------------------------
    pp = [c['pp'] for c in CALLS if c['pp']]; tg = [c['tg'] for c in CALLS if c['tg']]
    say('## 3. Rechenleistung', '',
        f'- {len(CALLS)} Aufrufe, Eingabe Ø {sum(c["in"] for c in CALLS) / len(CALLS):.0f} Tokens, Ausgabe Ø {sum(c["out"] for c in CALLS) / len(CALLS):.0f} Tokens',
        f'- Eingabe lesen: Ø {sum(pp) / max(1, len(pp)):.0f} Tokens/s · Text erzeugen: Ø {sum(tg) / max(1, len(tg)):.1f} Tokens/s', '')
    text = '\n'.join(OUT)
    Path(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null')).write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
