# RSS-Quellenlisten recherchieren

Der manuell startbare GitHub-Actions-Workflow **Research feed catalogues** prüft
Nachrichtenquellen und Behörden-/Blaulichtquellen in zwei getrennten Jobs.
Bei der Auswahl `both` laufen sie parallel. Ergebnisse werden als Artefakte
bereitgestellt; Quellen werden nicht automatisch in der Sendung aktiviert.

[Workflow im Repository](https://github.com/ploeffler/PersonalNewsHost/actions/workflows/research-feed-catalogs.yml)

1. Unter **Actions → Research feed catalogues → Run workflow** die Gruppe wählen:
   `news`, `authorities` oder `both`.
2. Nach Abschluss die Artefakte `feed-research-news` und/oder
   `feed-research-authorities` herunterladen. Aufbewahrungszeit: 14 Tage.
3. JSON, OPML, Quellenübersicht und Prüfprotokoll prüfen. Bestätigte Änderungen
   können anschließend per Pull Request ins Repository übernommen werden.

Die aktuell eingecheckten Quellenlisten:

- [Nachrichtenportale DE / EN](rss-quellenliste.md)
- [Polizei, Feuerwehr, Rettung und Warnquellen DE / AT](polizei-rss-quellenliste.md)

Für Landeswarnzentralen und andere Quellen ohne bestätigtes RSS/Atom sind die
Webseiten oder dokumentierten APIs separat vermerkt. Ein leeres Warnfeed ist
kein automatisch defekter Feed; Gefahrenlage und Entwarnung werden dadurch
nicht beurteilt. Die Sendungsanbindung solcher Warnungen bleibt ein eigener
Arbeitsschritt.

[Technik, lokale Ausführung und Fehlerverhalten](../../research/README.md)
