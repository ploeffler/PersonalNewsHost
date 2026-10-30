# RSS-Recherche für PersonalNewsHost

Stand: 28. Oktober 2026. Rechercheauftrag: breite Auswahl etablierter
Nachrichtenportale mit deutscher oder englischer Feedsprache. Es wurde keine
Reichweitenrangliste erstellt und keine aktive Quellenwahl geändert.

Ergebnisse:

- `../../docs/guide/rss-quellenliste.md`: lesbare Liste mit Anbietern,
  Herkunftsländern, Themen, Feed-Adressen und Prüfhinweisen.
- `../../docs/feed-catalog.json`: vollständiger Katalog als Grundlage für eine
  spätere Auswahloberfläche; alle Einträge standardmäßig deaktiviert.
- `../../docs/feed-catalog.opml`: Importdatei mit aktuellen, technisch bestätigten
  Feeds ohne zusätzlichen Prüfhinweis.
- `feed-research-raw.json`: Prüfergebnisse sämtlicher Kandidaten einschließlich
  fehlgeschlagener Abrufe. Fehlende Erreichbarkeit bei dieser Prüfung beweist
  keine generelle Abschaltung.

Reproduzieren, mit Python 3 und Internetzugang:

```bash
python3 research/rss/collect.py
python3 research/rss/supplement.py
python3 research/rss/build_catalog.py
```

Die Erkennung liest offizielle Verzeichnisse und HTML-Feedverweise, ergänzt
bekannte Kandidaten und prüft die XML-Struktur sowie Meldungsdaten. Sprache und
Herkunftsland basieren auf Feed-Metadaten beziehungsweise der Anbieterfassung.
Themen und die vorgeschlagenen Bereiche Allgemein/Wirtschaft/Lokales sind
heuristische Vorschläge. OPML enthält nur Einträge mit `verified_recent`.
Andere Einträge im JSON haben `review` und konkrete Prüfhinweise. Die Schwelle
für „aktuell“ beträgt 14 Tage; das ist keine Aussage über eine Einstellung des
Angebots. Nutzungsbedingungen bleiben anbieterspezifisch.

Die Skripte verwenden ausschließlich die Python-Standardbibliothek und
benötigen keine Zugangsdaten. Acht parallele Abrufe, maximal zwei Megabyte je
Antwort und zwölf Sekunden Netzwerk-Timeout begrenzen die Recherche.
