# Startseite im Redaktionslayout

Die Startseite (`docs/index.html`) besteht aus diesen Teilen:

| Bereich | Inhalt | Quelle |
| --- | --- | --- |
| Eilmeldungsleiste | Rotes Band mit der neuesten Eilmeldung der letzten Stunden, Link zum Kurzupdate | `breaking-banner.js`, `short-updates.json` (T013) |
| Aufmacher | Aktuelle Sendung als Video mit Untertiteln, Playlist mit Sendungen und Kurzupdates | `generate.py`, `playlist.js` |
| Meldungen dieser Sendung | Links auf die Artikelseiten der aktuellen Sendung | `article_pages.py` (T020) |
| Rubriken | Je Rubrik die vier neuesten Schlagzeilen der letzten 24 Stunden | `homepage.py`, `news-store.json` |
| Neueste Beiträge | Die sechs neuesten Schlagzeilen aus allen Quellen | `homepage.py`, `news-store.json` |
| Nachrichten | Alle Meldungen der letzten 24 Stunden mit Text | `news-list.js` |

## Rubriken

Die Rubriken sind die Sendungsbereiche aus `editorial.broadcast_sections`: zuerst die feste Zuordnung eines Feeds (`feed_sections`), dann Stichwörter in der Schlagzeile (`keywords`), sonst die Standardrubrik. Rubriken ohne Meldung werden ausgelassen. Ist eine Meldung Teil der aktuellen Sendung, führt der Link auf ihre Artikelseite, sonst zum Originalartikel.

Rubriken und „Neueste Beiträge“ sind statisches HTML zwischen `<!-- pnh:blocks:start -->` und `<!-- pnh:blocks:end -->`. Sie funktionieren ohne JavaScript und werden bei jeder Sendung und bei jedem RSS-Lauf (`collect_news.py`) neu geschrieben. Von Hand:

```sh
python3 scripts/homepage.py --refresh docs
```

## Hell- und Dunkelmodus

`docs/site.css` legt alle Farben als CSS-Variablen fest (`--bg`, `--surface`, `--text`, `--muted`, `--link`, …). `playlist.css` und `news-list.css` verwenden nur noch diese Variablen. Ohne eigene Wahl folgt die Seite der Systemeinstellung (`prefers-color-scheme`). Der Knopf „Dunkles Design“ (`theme.js`) schaltet um und merkt sich die Wahl im Browser; er ist per Tastatur bedienbar und meldet den Zustand mit `aria-pressed`.

## Barrierefreiheit

- Überschriftenhierarchie und Abschnitte mit `aria-labelledby`, Listen für Schlagzeilen, `<time>` mit maschinenlesbarer Zeit
- Sichtbarer Fokusrahmen für Links, Knöpfe und Video
- Kontraste im hellen und dunklen Modus nach WCAG AA
- Logo mit Alternativtext; Untertitel für das Video

Automatische Prüfung: Der Workflow `foundation-ci.yml` erzeugt die Blöcke auf einer Kopie von `docs/` und prüft die Seite mit axe-core (WCAG 2.1 A/AA) im hellen und dunklen Modus (`tests/test_homepage_a11y_browser.cjs`). Der Lauf scheitert bei Verstößen der Stufen „critical“ oder „serious“. Zusätzlich wird geprüft, dass der Design-Knopf per Tastatur funktioniert.

Lokal:

```sh
npm install --no-save --prefix=/tmp/a11y axe-core@4.10.3 playwright-core@1.56.1
cp -r docs /tmp/site && python3 scripts/homepage.py --refresh /tmp/site
SITE_DIR=/tmp/site NODE_PATH=/tmp/a11y/node_modules node tests/test_homepage_a11y_browser.cjs
```
