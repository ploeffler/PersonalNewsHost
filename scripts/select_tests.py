#!/usr/bin/env python3
"""Tests für einen Pull Request nach den geänderten Dateien auswählen.

Übernommen aus GhostWriter (#439, #485) und auf PersonalNewsHost zugeschnitten:
Ein Pull Request, der nur Doku oder einzelne Skripte ändert, lässt nur die
Python-Tests laufen, die diese Dateien betreffen. ffmpeg wird nur installiert,
wenn ein ausgewählter Test es braucht; die Browser-Tests laufen nur, wenn sich
Seiten unter docs/ (HTML, JS, CSS) oder ein *.cjs-Test geändert haben.

Im Zweifel die volle Suite: bei Workflows, config-Dateien, gelöschten oder
umbenannten Dateien, Skripten ohne zugeordneten Test und wenn mehr als 60 %
der Tests betroffen wären.

  python3 scripts/select_tests.py --files <datei> [--removed <datei>] [--github-output <datei>]

Ausgabe: mode=full|subset|none, tests=<module>, ffmpeg=0|1, browser=0|1.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / 'tests'

FULL_FILES = {'config.json', 'config.example.json', 'requirements.txt'}
FULL_PREFIXES = ('.github/', 'tests/fixtures/', 'tests/data/', 'assets/')
# reine Text-/Datenänderungen ohne Python-Bezug
DOC_SUFFIXES = ('.md', '.txt', '.png', '.jpg', '.svg', '.opml')
BROWSER = re.compile(r'^docs/.*\.(html|js|css)$|^tests/.*\.cjs$')
FFMPEG = re.compile(r'ffmpeg|ffprobe')
FULL_SHARE = 0.6


def test_files():
    return sorted(TESTS.glob('test_*.py'))


def users_of(module, files):
    pattern = re.compile(rf'\b{re.escape(module)}\b')
    return {f.stem for f in files if pattern.search(f.read_text(encoding='utf-8'))}


def importers(module, scripts=None):
    """Das Skript selbst und alle Skripte, die es direkt oder über andere importieren."""
    scripts = sorted((ROOT / 'scripts').glob('*.py')) if scripts is None else scripts
    text = {f.stem: f.read_text(encoding='utf-8') for f in scripts}
    found, todo = {module}, [module]
    while todo:
        name = todo.pop()
        pattern = re.compile(rf'^\s*(?:from\s+{re.escape(name)}\s+import|import\s+(?:[\w, ]*,\s*)?{re.escape(name)}\b)', re.M)
        for stem, body in text.items():
            if stem not in found and pattern.search(body):
                found.add(stem)
                todo.append(stem)
    return found


def mentioned_by(path, files):
    """Tests, die den Pfad als Zeichenkette nennen (z. B. 'docs/news-list.js')."""
    pat = re.compile(rf"""['"/]{re.escape(Path(path).name)}['"]""")
    return {f.stem for f in files if pat.search(f.read_text(encoding='utf-8'))}


def select(changed, removed=(), files=None):
    """Liefert (mode, tests, ffmpeg, browser)."""
    files = test_files() if files is None else files
    known = {f.stem for f in files}
    browser = any(BROWSER.search(p) for p in list(changed) + list(removed))
    if not changed or removed:
        return 'full', [], True, True
    chosen = set()
    for path in changed:
        name = Path(path).name
        if path in FULL_FILES or path.startswith(FULL_PREFIXES):
            return 'full', [], True, True
        elif path.startswith('tests/') and name.startswith('test_') and name.endswith('.py'):
            chosen.add(Path(path).stem)
        elif path.startswith('tests/') and name.endswith('.cjs'):
            continue
        elif path.startswith('scripts/') and path.endswith('.py') and path.count('/') == 1:
            stem = Path(path).stem
            if not users_of(stem, files):
                return 'full', [], True, True
            for module in importers(stem):
                chosen |= users_of(module, files)
        elif path.startswith('docs/'):
            chosen |= mentioned_by(path, files)
        elif path.endswith(DOC_SUFFIXES) or path.startswith(('research/', '.state/')):
            continue
        else:
            return 'full', [], True, True
    chosen &= known
    if not chosen:
        return 'none', [], False, browser
    if len(chosen) > FULL_SHARE * len(known):
        return 'full', [], True, True
    by_stem = {f.stem: f for f in files}
    ffmpeg = any(FFMPEG.search(by_stem[t].read_text(encoding='utf-8')) for t in chosen)
    return 'subset', sorted(chosen), ffmpeg, browser


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--files', required=True)
    ap.add_argument('--removed')
    ap.add_argument('--github-output')
    a = ap.parse_args(argv)
    read = lambda p: [l.strip() for l in Path(p).read_text(encoding='utf-8').splitlines() if l.strip()] if p else []
    mode, tests, ffmpeg, browser = select(read(a.files), read(a.removed))
    lines = [f'mode={mode}', f'tests={" ".join(tests)}', f'ffmpeg={int(ffmpeg)}', f'browser={int(browser)}']
    print('\n'.join(lines))
    if a.github_output:
        with open(a.github_output, 'a', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
