# Quellenrecherche als GitHub-Actions-Workflow

Der Workflow **Research feed catalogues** (`.github/workflows/research-feed-catalogs.yml`)
recherchiert die beiden Quellengruppen getrennt:

- `news`: deutsch- und englischsprachige Nachrichtenportale, Ressort- und
  Regionalfeeds.
- `authorities`: Polizei, Feuerwehr, Rettungsdienste, THW/Katastrophenschutz,
  Landeswarnzentralen und öffentliche Warnquellen in Deutschland und Österreich.

## In GitHub starten

1. Nach Übernahme des Workflows in den Default-Branch im Repository **Actions**
   öffnen und **Research feed catalogues** wählen.
2. **Run workflow** anklicken, Branch auswählen und `both`, `news` oder
   `authorities` einstellen.
3. Nach Abschluss die Artefakte `feed-research-news` beziehungsweise
   `feed-research-authorities` herunterladen. Sie werden 14 Tage aufbewahrt.

Bei `both` laufen beide Jobs auf getrennten Runnern. Es gibt keinen automatischen
Zeitplan. Der Workflow benötigt ausschließlich Lesezugriff auf das Repository,
keine Secrets, keine Drittanbieterpakete und keine Zugangsdaten zu den Quellen.
Er aktiviert keine Quellen, aktualisiert nicht die Sendungskonfiguration und
schreibt keine automatisch recherchierten Daten zurück auf `main` oder GitHub
Pages.

## Ergebnisse prüfen

Ein erfolgreiches Artefakt enthält die ursprünglichen Repository-Pfade:

- `docs/*feed-catalog.json`: Quellen, Sprache, Region, Format, Prüfstatus.
- `docs/*feed-catalog.opml`: importierbare bestätigte Quellen.
- `docs/guide/*rss-quellenliste.md`: lesbare Quellenübersichten.
- `research/…/*.json`: Fundstellen und technische Prüfprotokolle.
- `manifest.json`: Gruppe, Laufmodus, Start/Ende und Validierung.
- `run.log`: Protokoll der einzelnen Schritte.

Der Behördenjob enthält zusätzlich offizielle Web-/API-Quellen ohne bestätigten
RSS-/Atom-Feed. Diese werden nicht als RSS importiert. Warnfeeds werden von
Einsatz- und Organisationsmeldungen unterschieden; leere Warnfeeds können regulär
sein. Vor Verwendung in einer Sendung benötigen Warnungen eine gesonderte
Auswertung von Gebiet, Gültigkeit, Updates und Entwarnungen.

Die eingecheckten Kataloge sind der Ausgangsstand vom 28. Oktober 2026.
Neue Läufe datieren die Ergebnisse neu. Netzwerkausfälle einzelner Quellen werden
im Prüfprotokoll sichtbar; eine fehlgeschlagene Prüfung beweist keine Einstellung
eines Angebots. Leere Kataloge, Dubletten, abweichende OPML-Dateien oder eine
ungewollte automatische Aktivierung lassen die Validierung fehlschlagen.

Ein fehlgeschlagener Lauf exportiert Fehlerprotokoll und Manifest, aber keine
alten Katalogdateien als vermeintlich neue Recherche. Vorhandene Artefaktordner
werden nicht überschrieben. Es erfolgt keine automatische Wiederholung bei
HTTP 503. Nach hinreichendem Abstand kann eine neue Recherche gestartet werden.

Bestätigte Ergebnisse können nach redaktioneller Prüfung aus dem Artefakt an den
gleichen Pfaden übernommen und per Pull Request aktualisiert werden.

## Lokal ausführen

Python 3.12 oder neuer und Internetzugang genügen:

```bash
python3 -B research/run.py --group news --output-dir /tmp/news-research
python3 -B research/run.py --group authorities --output-dir /tmp/authority-research
```

Die Ausgabeordner müssen neu sein. Für die reine Prüfung der gespeicherten
Recherche ohne Netzwerkzugriff:

```bash
python3 -B research/run.py --group news --offline --output-dir /tmp/news-snapshot
python3 -B research/run.py --group authorities --offline --output-dir /tmp/authority-snapshot
python3 -m unittest discover -s tests -p test_feed_research.py
```

Offline-Artefakte tragen ausdrücklich `mode: stored_snapshot`; das Datum des
geprüften Ausgangsstandes bleibt erhalten. Detailinformationen zu den
Recherche-Skripten stehen in [Nachrichten](rss/README.md) und
[Behörden/Blaulicht](police-rss/README.md).
