# Eilmeldungs-Modus

Der Workflow `short-updates.yml` prüft die RSS-Feeds viertelstündlich nach Zeitplan (kein Dauerbetrieb). Findet er eine Eilmeldung, entsteht ein Kurzclip von höchstens 60 Sekunden. Die Eilmeldung erscheint als rotes Band oben auf der Startseite und als erster Eintrag in `feed.xml`. Ohne Treffer entsteht kein Video, und der Lauf installiert weder Sprachausgabe noch FFmpeg.

## Ablauf eines Laufs

1. `python3 scripts/short_updates.py --plan <Datei>` liest die Feeds, wendet die Regeln an und schreibt `media=true|false` in die Workflow-Ausgabe. Es werden keine Dateien in `docs/` verändert.
2. Nur bei `media=true` werden `espeak-ng`, `ffmpeg` und Pillow installiert.
3. `python3 scripts/short_updates.py --from-plan <Datei>` verwendet dieselben Kandidaten und denselben Zeitpunkt, erzeugt Text, Sprachausgabe und Clip und veröffentlicht:
   - `docs/short-updates.json` und die Seite `short-updates.html` (Anker `#update-<ID>`)
   - Eilmeldungen zuerst in `docs/feed.xml` (Titel „Eilmeldung: …“, Kategorie `Eilmeldung`, Video als Anhang). Ältere Eilmeldungseinträge werden ersetzt; die Sendung bleibt im Feed.
   - Ein Platzhalter für das Band auf der Startseite. `docs/breaking-banner.js` lädt `short-updates.json` und zeigt die neueste Eilmeldung der letzten Stunden an.

Eine neue Sendung übernimmt aktuelle Eilmeldungen ebenfalls in `feed.xml` und setzt den Platzhalter für das Band.

## Konfiguration

```json
"short_updates": {
  "enabled": true,
  "freshness_minutes": 60,
  "interval_minutes": 15,
  "breaking": {
    "keywords": ["eilmeldung", "breaking", "+++", "evakuier*", "…"],
    "exclude_keywords": [],
    "sources": [],
    "min_sources": 1,
    "max_per_day": 6,
    "max_clip_seconds": 60,
    "banner_hours": 3,
    "timezone": "Europe/Vienna"
  }
}
```

| Schlüssel | Bedeutung |
| --- | --- |
| `keywords` | Stichwörter im Titel, ohne Beachtung von Groß- und Kleinschreibung, als ganzes Wort. `wort*` erlaubt beliebige Endungen (`evakuier*` trifft „evakuiert“, „Evakuierung“). Fehlt der Schlüssel, gilt die bisherige Standardliste. |
| `exclude_keywords` | Titel mit einem dieser Wörter sind nie Eilmeldungen (z. B. `übung*`). Gilt auch für Eilmeldungsquellen. |
| `sources` | Eilmeldungsquellen: Feed-URLs (exakt) oder Hostnamen (inkl. Subdomains). Jede frische Meldung daraus gilt als Eilmeldung, auch ohne Stichwort. |
| `min_sources` | Schwelle 1–5: So viele verschiedene Anbieter müssen innerhalb von `freshness_minutes` eine ähnliche Schlagzeile bringen, bevor ein Stichworttreffer zählt. `2` verringert Fehlalarme. |
| `max_per_day` | Höchstens so viele Eilmeldungen pro Kalendertag (0–48, Zeitzone `timezone`). |
| `max_clip_seconds` | Obergrenze der Cliplänge, höchstens 60 Sekunden. Längere Sprachausgabe wird abgeschnitten. |
| `banner_hours` | So lange steht das Band auf der Startseite (0 = kein Band). |

Weiterhin gilt: höchstens ein neues Update pro Lauf, mindestens `interval_minutes` Abstand, ähnliche Schlagzeilen werden nur einmal gemeldet, und der Text besteht nur aus Sätzen der Quelle. Jedes Update speichert den Grund (`reason`: `Quelle` oder `Stichwort`).
