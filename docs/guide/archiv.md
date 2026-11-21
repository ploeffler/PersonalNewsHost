# Archiv

Jede fertige Sendung kommt ins Archiv. Es gibt zwei Ebenen:

| Ebene | Ort | Inhalt | Aufbewahrung |
| --- | --- | --- | --- |
| Archivindex und Archivseite | `docs/archive.json`, `docs/archive.html` (öffentlich) | Metadaten: Datum, Uhrzeit, Show, Titel, Meldungen mit Artikelseite und Quellen, Videolink | dauerhaft |
| Dauerhafter Videospeicher | konfigurierter Archivpfad (nicht öffentlich) | Video, Transkript, Untertitel, `manifest.json` | dauerhaft, keine automatische Löschung |
| Veröffentlichungskopien | `docs/broadcasts/` | Video, Transkript, Untertitel der letzten zwei Sendungen für Playlist und Artikelseiten | temporär, rotieren |

## Archivpfad

Videos werden nur dauerhaft gespeichert, wenn ein Archivpfad angegeben ist:

```json
"archive": {
  "path": "/srv/pnh-archiv"
}
```

oder über die Umgebungsvariable `PNH_ARCHIVE_PATH` (hat Vorrang). Relative Pfade gelten ab dem Projektordner. Ohne Pfad entsteht nur der Archivindex. In GitHub Actions ist der Runner nach jedem Lauf weg; ein Archivpfad ist dort nur sinnvoll auf einem eigenen Runner oder eingebundenen Speicher.

Ablage pro Sendung:

```
<archivpfad>/JJJJ/MM/TT/<show_id>/<sendungs_id>/
    video.mp4  transcript.txt  subtitles.de.vtt  subtitles.de.srt  manifest.json
```

- Das Datum ist das lokale Datum in der Zeitzone der Show (`automation.timezone`); eine Sendung um 0:30 Uhr in Wien am 1. Jänner liegt also unter `JJJJ/01/01`, obwohl es in UTC noch der 31. Dezember ist. `manifest.json` enthält UTC-Zeit, Zeitzone, Meldungen, Quellen sowie Größe und SHA-256 jeder Datei.
- `show_id` ist `main` für die Standardsendung, sonst die Show-ID aus `produce_show.py`. Mehrere Sendungen am selben Tag liegen nebeneinander.
- Jede Datei wird zuerst als `.part` geschrieben, geprüft und dann ohne Überschreiben abgeschlossen. Wiederholt man denselben Schritt, passiert nichts. Weicht eine vorhandene Datei ab, bricht die Archivierung ab.
- Schlägt die Archivierung fehl (Speicher voll, keine Schreibrechte, Konflikt), wird die neue Ausgabe nicht veröffentlicht; die letzte Ausgabe bleibt bestehen.

## Nicht löschbar

Archivierte Videos werden nie automatisch gelöscht, und die Oberfläche (Konfigurationsseite, Sender-Stil-Server, Webseiten) bietet keine Funktion zum Löschen von Archivdateien. Löschen ist nur direkt auf dem Speicher durch den Betreiber möglich. Bereinigt werden ausschließlich temporäre Dateien: die Veröffentlichungskopien in `docs/broadcasts/`, Artikelordner der dort nicht mehr vorhandenen Sendungen, Render-Zwischendateien und Caches (`.cache/`).

## Archivseite

`archive.html` listet alle Sendungen nach Datum (neueste zuerst). Video- und Artikellinks erscheinen, solange die öffentliche Kopie existiert; dauerhaft archivierte Sendungen sind gekennzeichnet. Die Startseite verlinkt das Archiv.

## Größe

Der Archivindex wächst um etwa 1–2 kB pro Sendung, bei drei Sendungen am Tag also um rund 2 MB pro Jahr. Videos liegen nicht dauerhaft im Repository; GitHub empfiehlt Repositories unter 1 GB und begrenzt Pages-Sites auf 1 GB.
