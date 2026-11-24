"""Kennzeichnung als automatisch erstellt mit KI-Unterstützung (T050).

* ``docs/ueber-diese-sendung.html``: Funktionsweise, Grenzen und Korrekturkontakt
  (``about.correction_contact`` in der Konfiguration, sonst Verweis auf das Impressum).
* Startseite: Hinweisblock direkt beim Video mit Link auf die Seite.
* Artikelseiten: Hinweisblock mit Abrufzeit der Quellen (Zeit der Sendung, für
  die die Quellen abgerufen wurden), Quellen und Link auf die Seite. Quelle und
  Link zum Original stehen bereits auf der Artikelseite (T020).
* ``missing_disclosure`` meldet Seiten ohne Kennzeichnung.

Die Kennzeichnung im Bild des Videos selbst folgt mit T280, synthetische
Stimmen und Avatare mit T145/T167. Die Blöcke liegen zwischen festen Markern und
werden bei jedem Lauf ersetzt (Wiederholung ist ein No-op).
"""
import html
import re
from pathlib import Path

ABOUT_PAGE = 'ueber-diese-sendung.html'
START, END = '<!-- pnh:ki:start -->', '<!-- pnh:ki:end -->'
ARTICLE_DIR = 'artikel'
LABEL = 'Automatisch erstellt mit KI-Unterstützung'
TIME = re.compile(r"<time datetime=['\"]([^'\"]+)['\"][^>]*>([^<]*)</time>")


def correction_contact(config):
    raw = str(((config.get('about') or {}).get('correction_contact')) or '').strip()
    return raw[:300]


def render_about(config):
    esc = html.escape
    site = esc(str(config.get('title', 'PersonalNewsHost')))
    contact = correction_contact(config)
    contact_html = (f'<p>{esc(contact)}</p>' if contact else
                    "<p>Der Korrekturkontakt steht im <a href='impressum.html'>Impressum</a>.</p>")
    return ("<!doctype html><html lang='de'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Über diese Sendung – {site}</title><link rel='stylesheet' href='site.css'>"
            "<style>body{font:1.05rem/1.6 system-ui;max-width:760px;margin:2rem auto;padding:0 1rem}</style></head>"
            "<body><main><nav><a href='index.html'>← Zur Startseite</a></nav><h1>Über diese Sendung</h1>"
            f"<p><strong>{LABEL}.</strong> Sendungen, Seiten und Texte von {site} entstehen automatisch aus öffentlichen "
            "RSS-Meldungen. Redaktionell geprüft werden sie nicht einzeln.</p>"
            "<h2>Funktionsweise</h2><ol><li>Meldungen werden aus den konfigurierten RSS-Quellen abgerufen.</li>"
            "<li>Eine Auswahl wird thematisch zusammengefasst und von Software zu kurzen Sprechertexten verarbeitet.</li>"
            "<li>Synthetische Sprache, ein virtueller Moderator und Grafiken ergeben das Video.</li>"
            "<li>Jede Meldung verweist auf ihre Quellen und das Original.</li></ol>"
            "<h2>Grenzen</h2><ul><li>Zusammenfassungen können Fehler, Verkürzungen oder Auslassungen enthalten.</li>"
            "<li>Inhalte werden nicht unabhängig überprüft; maßgeblich ist die verlinkte Originalquelle.</li>"
            "<li>Stimme und Moderator sind synthetisch und stellen keine echte Person dar.</li></ul>"
            f"<h2>Korrekturen</h2>{contact_html}"
            "<nav aria-label='Rechtliches'><a href='datenschutz.html'>Datenschutz</a> · <a href='impressum.html'>Impressum</a></nav>"
            "</main><script src='theme.js'></script></body></html>\n")


def _block(prefix, retrieved=''):
    esc = html.escape
    when = (f"<p class='ki-meta'>Quellen abgerufen für die Sendung vom {esc(retrieved)}.</p>" if retrieved else '')
    return (START + f"<aside class='ki-hinweis' aria-label='Kennzeichnung' style='border:1px solid currentColor;border-radius:8px;padding:.5rem .8rem;margin:1rem 0;font-size:.9rem'><p><strong>{LABEL}.</strong> "
            f"Inhalte können Fehler enthalten. <a href='{prefix}{ABOUT_PAGE}'>Über diese Sendung</a></p>{when}</aside>" + END)


def _place(page, block, anchors):
    if START in page and END in page:
        return page[:page.index(START)] + block + page[page.index(END) + len(END):]
    for anchor, before in anchors:
        if anchor in page:
            return page.replace(anchor, (block + anchor) if before else (anchor + block), 1)
    return page


def _retrieved(page):
    found = TIME.search(page)
    return found.group(2).strip() if found else ''


def update_disclosure(docs, config):
    docs = Path(docs)
    about = render_about(config)
    target = docs / ABOUT_PAGE
    if not target.is_file() or target.read_text(encoding='utf-8') != about:
        target.write_text(about, encoding='utf-8')
    home = docs / 'index.html'
    if home.is_file():
        page = home.read_text(encoding='utf-8')
        updated = _place(page, _block(''), [('</video>', False), ('<h2>Quellen</h2>', True), ('</main>', True)])
        if updated != page:
            home.write_text(updated, encoding='utf-8')
    for path in sorted((docs / ARTICLE_DIR).rglob('*.html')) if (docs / ARTICLE_DIR).is_dir() else []:
        page = path.read_text(encoding='utf-8')
        depth = len(path.relative_to(docs).parts) - 1
        updated = _place(page, _block('../' * depth, _retrieved(page)),
                         [("<section aria-label='Quellen'>", True), ('</article>', True), ('</main>', True)])
        if updated != page:
            path.write_text(updated, encoding='utf-8')
    return about


def missing_disclosure(docs):
    """Relative paths of the start page and article pages that lack the label."""
    docs = Path(docs)
    pages = ['index.html'] if (docs / 'index.html').is_file() else []
    pages += [p.relative_to(docs).as_posix() for p in sorted((docs / ARTICLE_DIR).rglob('*.html'))] \
        if (docs / ARTICLE_DIR).is_dir() else []
    return [rel for rel in pages if LABEL not in (docs / rel).read_text(encoding='utf-8')]
