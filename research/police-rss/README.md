# Polizei, Feuerwehr, Rettungsdienst und Warnquellen DE / AT

Recherche vom 28. Oktober 2026. Keine Änderung an der aktiven Quellenauswahl.
Die bisherigen Dateinamen `police-feed-catalog.*` bleiben als gemeinsame Liste
erhalten; `schema_version: 2` ergänzt Kategorien und Warnungsmetadaten.

Ausgaben:

- `../../docs/guide/polizei-rss-quellenliste.md`: lesbare Gesamtliste.
- `../../docs/police-feed-catalog.json`: Polizei, Feuerwehr, Rettungsdienst,
  Katastrophenschutz und Warnfeeds in `feeds`. `non_feed_sources` enthält
  zusätzliche offizielle Web-/API-Quellen ohne bestätigten spezifischen Feed.
- `../../docs/police-feed-catalog.opml`: aktuelle Nachrichtenfeeds und technisch
  verfügbare Warnfeeds, nach Kategorie und Land gruppiert. Gemischte
  Blaulicht-Länderfeeds bleiben gesondert unter `mixed_feeds` im JSON.
- `checks.json`, `discovery.json`: ursprüngliche Polizeirecherche einschließlich
  der damals ausgeschlossenen nichtpolizeilichen Dienststellen.
- `emergency-checks.json`: zusätzliche Quellenprüfung für die Erweiterung.

Reproduzieren, mit Python 3 und Internetzugang:

```bash
python3 research/police-rss/discover.py
python3 research/police-rss/collect.py
# Optional später: einmalige Nachprüfung vorübergehender HTTP-503-Fehler
python3 research/police-rss/recheck.py
python3 research/police-rss/collect_emergency.py
python3 research/police-rss/build_catalog.py
```

`build_catalog.py` übernimmt die Erweiterung automatisch, wenn
`emergency-checks.json` existiert. `extend_catalog.py` kann auch separat laufen.
Feuerwehr- und THW-Dienststellen aus der ursprünglichen Recherche werden aus
bereits gespeicherten Prüfergebnissen übernommen, ohne erneuten Massenabruf.

Presseportal-Abrufe sind begrenzt. HTTP-503-Fehler werden nicht automatisch in
einer Schleife wiederholt. `recheck.py` ist eine separate Nachprüfung.
Fehlerhafte oder nicht vollständig geladene Antworten sind keine bestätigten
Feeds. Für den großen offiziellen DRK-Newsfeed gilt eine dokumentierte
Lesebegrenzung von acht statt zwei Megabyte.

Bei Nachrichten bedeutet `verified_recent`: mindestens eine auswertbar datierte
Meldung innerhalb von 14 Tagen. Selten berichtende Organisationen können mit
`review` weiterhin technisch lesbare Feeds haben.

Warnfeeds werden anders behandelt: `verified_warning_feed` bestätigt nur das
Format und die Erreichbarkeit; `available_empty` bezeichnet einen technisch
lesbaren, leeren Warnfeed. Beide Statuswerte bestätigen weder eine derzeitige
Gefahrenlage noch eine Entwarnung. `requires_warning_adapter: true` kennzeichnet,
dass vor automatischer Sendungsverwendung insbesondere Gebiet, Gültigkeit,
Status, Aktualisierung und Aufhebung einer Warnung geprüft werden müssen.

`non_feed_sources` und allgemeine Landesnachrichten sind keine erfundenen
Alarm-RSS-Adressen. Öffentliche Lageübersichten können verspätet und unvollständig
sein. Ebenso sind Presseberichte von Feuerwehr und Rettungsorganisationen keine
vollständigen Echtzeit-Einsatzprotokolle. Alle Quellen bleiben standardmäßig
deaktiviert. Nutzungsbedingungen sind anbieterspezifisch.
