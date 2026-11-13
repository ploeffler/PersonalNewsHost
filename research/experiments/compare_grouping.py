#!/usr/bin/env python3
"""Experiment (nicht produktiv): Sendungstext nach geltenden Regeln vs. mit
languagemodels-Embeddings (multilingual-e5-small) fuer Gruppierung und
Wiederholungserkennung. Der vorgelesene Text bleibt in beiden Varianten
woertlich belegt; verify() bleibt unveraendert aktiv."""
import importlib.util, itertools, json, os, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
T_EVENT = float(os.environ.get('T_EVENT', '0.90'))
T_SENT = float(os.environ.get('T_SENT', '0.93'))
LIMIT = 5


def load_pipeline():
    spec = importlib.util.spec_from_file_location('ep', ROOT / 'scripts/editorial_pipeline.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def build(p, store, now):
    report = p.prepare(store, now)
    selected = p.select(report, LIMIT)
    return report, selected


def stats(p, report):
    groups = report['groups']
    multi = [g for g in groups if p.publisher_count(report, g) > 1]
    return {'gruppen': len(groups), 'mehrquellen': len(multi),
            'mehrquellen_freigegeben': sum(g['verification']['status'] == 'approved' for g in multi),
            'zurueckgestellt': sum(g['verification']['status'] != 'approved' for g in groups)}


def script(p, report, selected):
    out = []
    for i, g in enumerate(selected, 1):
        out.append(f"{i}. [{p.publisher_count(report, g)} Quelle(n)] " + g['draft']['text'].replace('\n', '\n   '))
    return '\n\n'.join(out)


def main():
    store = json.loads((ROOT / 'docs/news-store.json').read_text(encoding='utf-8'))
    now = store['updated_at']
    out = []

    # A: geltende Regeln
    p = load_pipeline()
    t0 = time.perf_counter(); rep_a, sel_a = build(p, store, now); t_a = time.perf_counter() - t0
    out += ['# Vergleich: geltende Regeln vs. languagemodels-Embeddings', '',
            f"Datenstand news-store.json: {time.strftime('%d.%m.%Y %H:%M UTC', time.gmtime(now))}, "
            f"{len(store['articles'])} Artikel. Schwellen: T_EVENT={T_EVENT}, T_SENT={T_SENT}.", '',
            '## A – geltende Regeln', '', f'Laufzeit {t_a:.1f}s · ' + json.dumps(stats(p, rep_a), ensure_ascii=False), '',
            '```', script(p, rep_a, sel_a), '```', '']

    # B: Embeddings
    import languagemodels as lm
    lm.config['embedding_model'] = 'multilingual-e5-small'
    p = load_pipeline()
    rule_same, rule_repeats = p.same_event, p.repeats
    arts = [a for a in store['articles'] if a.get('id') and a.get('title')]
    t0 = time.perf_counter()
    keys = {a['id']: 'query: ' + a['title'] + '. ' + p.lead(a) for a in arts}
    vec = dict(zip(keys, np.array(lm.embed(list(keys.values())))))
    t_emb = time.perf_counter() - t0
    sent_cache = {}

    def svec(text):
        if text not in sent_cache:
            sent_cache[text] = np.array(lm.embed('query: ' + text))
        return sent_cache[text]

    extra_pairs = []

    def same_event(first, second):
        if rule_same(first, second):
            return True
        a, b = vec.get(first['id']), vec.get(second['id'])
        if a is None or b is None:
            return False
        score = float(a @ b)
        if score < T_EVENT:
            return False
        pa = p.places(first['title'] + '. ' + first.get('text', ''))
        pb = p.places(second['title'] + '. ' + second.get('text', ''))
        if pa and pb and not pa & pb:
            return False
        extra_pairs.append((score, first['title'], second['title']))
        return True

    extra_repeats = []

    def repeats(sentence, old):
        if rule_repeats(sentence, old):
            return True
        score = float(svec(sentence) @ svec(old))
        if score >= T_SENT:
            extra_repeats.append((score, sentence, old))
            return True
        return False

    p.same_event, p.repeats = same_event, repeats
    t0 = time.perf_counter(); rep_b, sel_b = build(p, store, now); t_b = time.perf_counter() - t0
    out += ['## B – mit languagemodels (multilingual-e5-small) für Gruppierung und Wiederholungen', '',
            f'Laufzeit {t_b:.1f}s (+{t_emb:.1f}s Einbettung von {len(keys)} Artikeln) · ' + json.dumps(stats(p, rep_b), ensure_ascii=False), '',
            '```', script(p, rep_b, sel_b), '```', '']

    seen = set(); uniq = []
    for s, x, y in sorted(extra_pairs, reverse=True):
        k = tuple(sorted((x, y)))
        if k not in seen: seen.add(k); uniq.append((s, x, y))
    out += [f'## Nur durch Embeddings zusammengelegte Paare ({len(uniq)})', '']
    out += [f'- {s:.3f} · {x} ⟷ {y}' for s, x, y in uniq[:80]] + ['']
    seen = set(); ur = []
    for s, x, y in sorted(extra_repeats, reverse=True):
        if (x, y) not in seen: seen.add((x, y)); ur.append((s, x, y))
    out += [f'## Nur durch Embeddings als Wiederholung erkannte Sätze ({len(ur)})', '']
    out += [f'- {s:.3f} · „{x[:140]}“ ≈ „{y[:140]}“' for s, x, y in ur[:40]] + ['']

    # Kalibrierung: Score-Verteilung
    ids = list(vec)
    rng = np.random.default_rng(1)
    rand = [float(vec[ids[i]] @ vec[ids[j]]) for i, j in rng.integers(0, len(ids), (3000, 2)) if i != j]
    rule_scores = [float(vec[a['id']] @ vec[b['id']]) for a, b in itertools.combinations(arts, 2)
                   if p.publisher(a, []) != p.publisher(b, []) and rule_same(a, b)]
    q = lambda v: ' / '.join(f'{x:.3f}' for x in np.percentile(v, [5, 50, 95])) if v else '–'
    out += ['## Kalibrierung (Perzentile 5/50/95)', '',
            f'- Zufallspaare: {q(rand)}', f'- Paare, die schon die Regeln erkennen ({len(rule_scores)}): {q(rule_scores)}', '']

    text = '\n'.join(out)
    print(text)
    Path(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null')).write_text(text, encoding='utf-8')
    Path('vergleich.md').write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
