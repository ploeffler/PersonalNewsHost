# Shows – erste Grundlage in Version 0.1

Die bisherige `config.json` bleibt unverändert nutzbar: Ohne `shows` wird sie als Show `main` aufgelöst. Der bisherige Aufruf `python3 scripts/generate.py` und sein Ausgabeziel bleiben für solche Konfigurationen bestehen.

Eine explizite `shows`-Liste definiert mehrere Editionen. Jede Show hat eine eindeutige ID aus Kleinbuchstaben, Ziffern, Unterstrich oder Bindestrich. Einstellungen werden von der Basiskonfiguration geerbt; verschachtelte Objekte werden zusammengeführt, Listen vollständig ersetzt. Keine Show erbt Änderungen einer anderen Show. Unbekannte Showfelder werden abgelehnt.

## Beispiel und Aufruf

`config.shows.example.json` enthält die beiden Shows `main` und `technology`. Die Beispiele rufen ohne entsprechend konfigurierte Quellen keine erfolgreiche Produktion hervor; Zeitpläne sind deaktiviert.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_config.py config.shows.example.json
python3 scripts/produce_show.py --config config.shows.example.json --list
python3 scripts/produce_show.py --config /pfad/meine-config.json --show main
python3 scripts/produce_show.py --config /pfad/meine-config.json --show technology
```

Der neue Aufruf schreibt nach `out/main/` bzw. `out/technology/`. `--output-root /pfad/produktionen` ändert die gemeinsame Wurzel. Jede Show erhält eigene Video-, Text-, Untertitel-, Feed- und Metadatendateien sowie `show.json`. Der Showaufruf versendet keine Telegram-Nachrichten und führt keinen Git-Push aus. Das bisherige öffentliche `docs/` wird mit den Standardargumenten nicht verändert.

Links im Feed sind standardmäßig relativ (`./`). Mit `--base-url https://beispiel.invalid/shows/main/` kann ein späterer Auslieferungspfad gesetzt werden. Diese Option veröffentlicht selbst keine Dateien. Die neue Ausgabe ist noch kein vollständiges öffentlich auslieferbares Portal: zusätzliche CSS-/JS-Assets und veröffentlichte URLs werden in späteren Ausbaustufen behandelt.

## Einstellungen und Grenzen

- `title`, `feeds`, `max_items`, Sprache, Stimme, Medien- und Redaktionsparameter können pro Show überschrieben werden.
- `presenter` und `studio` sind in dieser ersten Stufe bestehende lokale Bildpfade für Portrait bzw. Hintergrund; Avatar-/Studio-IDs folgen mit deren Verwaltung.
- `schedule` übernimmt das bisherige `automation`-Format. Dieser Produktionsaufruf startet eine Show ausdrücklich; automatische Mehrshow-Zeitplanung folgt später.
- `target_duration_seconds` wird validiert und übernommen. Das bestehende Rendering garantiert damit noch keine exakte Zielzeit.
- Der gespeicherte Redaktionspfad erwartet seine Eingabedatei `news-store.json` im jeweiligen Showverzeichnis. Eingänge werden absichtlich nicht automatisch zwischen Shows kopiert. Das Beispiel verwendet deshalb den bisherigen RSS-Pfad (`editorial.pipeline.enabled: false`).
- Explizite Showkonfigurationen werden vom alten Generatoraufruf abgewiesen, damit er sie nicht unbemerkt ignoriert. Verwende `produce_show.py`.
- Die Einbindung des alten Renderers wird innerhalb dieses Prozesses serialisiert. Fehler stellen ursprüngliche Konfiguration, Ausgabeziel und Feed-Zeitstempel wieder her. Unterschiedliche Prozesse dürfen noch nicht gleichzeitig dieselbe Show produzieren; dauerhafte Job-Sperren folgen mit der Auftragsverwaltung.
- Atomare Ausgabeumschaltung, Pflichtarchiv und AI-Label sind spätere verbindliche Produktionsgates. Diese Entwicklungsstufe ist noch nicht zur unbeaufsichtigten Veröffentlichung freigegeben.

## Prüfungen

Tests prüfen Legacy-Verhalten, Vererbung, zwei getrennte Ausgaben, ungültige IDs, Schemas, Fehlerwiederherstellung und Symlink-Ausbruch. Ein FFmpeg-Integrationstest erzeugt mit lokalen Text-/Audiofixtures zwei getrennte Videos, ohne Netzwerk- oder KI-Aufrufe.

## Rubriken und Quellenregeln

`feed_categories` ordnet einer vollständigen Feed-URL eine Rubrik zu. Ohne Zuordnung lautet sie `general`. `category_filter` beschränkt eine Show auf ausgewählte Rubriken; eine leere Liste lässt alle Rubriken zu. Die Rubrik steht pro Beitrag in `story-groups.json` unter `category`. Bestehende Sendungsbereiche (`editorial.broadcast_sections`) bleiben davon getrennt.

```json
{
  "feed_categories": {"https://example.org/technik/rss": "technology"},
  "category_filter": ["technology"],
  "source_policy": {
    "blocked_domains": ["blocked.example"],
    "excluded_keywords": ["Werbung"],
    "weights": {"example.org": 2}
  }
}
```

Domänensperren prüfen Artikel- und Feedhost einschließlich Subdomains, aber nicht bloße Namensendungen (`notblocked.example` ist keine Subdomain von `blocked.example`). Ausschlusswörter werden ohne Beachtung der Großschreibung in Titel und Quelltext gesucht. Die Regeln gelten vor Auswahl und Sprache sowohl im RSS-Pfad als auch im gespeicherten Redaktionspfad.

Vorbereitete Mehrquellenbeiträge werden vollständig ausgeschlossen, wenn eine ihrer Quellen nicht zugelassen ist. Ihr bereits freigegebener Text wird nicht unter Entfernung einzelner Quellen weiterverwendet. Im Redaktionsbericht zeigt `selection_excluded` den Ausschluss; der faktische Prüfstatus wird dadurch nicht umgedeutet.

Quellengewichte von 0 bis 100 beeinflussen die Reihenfolge vor Aktualität, bei gleicher Gewichtung bleibt die bisherige Aktualitäts-/Quellenvielfalt-Auswahl bestehen. Default ist 1. Gewicht 0 ist **keine Sperre**; dafür dient `blocked_domains`. Bei überlappenden Gewichtungsregeln gilt die spezifischste Domäne. Keine Einstellung ersetzt die redaktionelle Fakten-/Freigabeprüfung. Es gibt noch keine KI-gestützte Neuzuordnung von Rubriken.
