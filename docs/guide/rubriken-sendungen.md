# Rubriken- und Sendungsseiten

Jede konfigurierte Rubrik und jede Sendung hat eine eigene statische Übersichtsseite mit Paginierung.

| Seite | Pfad | Inhalt |
| --- | --- | --- |
| Rubrik | `rubrik/<id>/index.html` | Meldungen aus `news-store.json`, neueste zuerst; Zuordnung wie auf der Startseite |
| Sendung | `sendung/<id>/index.html` | Ausgaben aus `archive.json` (Archiv), neueste zuerst |

* **Paginierung:** 20 Einträge je Seite; weitere Seiten heißen `page-2.html`, `page-3.html` … und sind mit „Neuere“/„Ältere“ verlinkt. Nicht mehr benötigte Seiten werden entfernt.
* **Navigation:** Brotkrumen (Start › Rubriken/Archiv › Seite) und eine Navigation zu allen Rubriken und Sendungen auf jeder Seite sowie auf der Startseite.
* **Rubriken:** `editorial.broadcast_sections.sections`. Leere Rubriken haben ebenfalls eine Seite. Ohne Konfiguration gibt es die Rubrik „Allgemein“.
* **Sendungen:** `shows` in der Konfiguration; ohne `shows` die Sendung `main`.
* **Aktualisierung:** bei jedem RSS-Lauf und jeder Sendung (`scripts/homepage.py` → `scripts/section_pages.py`).
* **Sicherheit:** Kennungen werden auf `a-z`, `0-9` und `-` reduziert, alle Texte maskiert, nur `http(s)`-Links.
