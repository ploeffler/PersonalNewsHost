# Artikelseiten pro Meldung

Jede Sendung erzeugt für jede Meldung eine eigene statische HTML-Seite. Die Seiten entstehen im Build-Schritt von `scripts/generate.py` und werden mit dem übrigen `docs/`-Ordner über GitHub Pages veröffentlicht. Es gibt keinen Laufzeit-Server.

## Inhalt einer Seite

- Titel der Meldung, Rubrik (Sendungsbereich und Kategorie) und Sendezeitpunkt (Europe/Vienna)
- Kurze Zusammenfassung: derselbe redaktionelle Text, der in der Sendung gesprochen wird, ohne die Rubrik-Ansage und auf höchstens 600 Zeichen an einem Satzende gekürzt. Volltexte aus den Quellen werden nicht übernommen.
- Link zum Originalartikel und Liste aller Quellen des Ereignisses
- Videoplayer mit Sprungmarke: Das archivierte Sendungsvideo `broadcasts/<ID>.mp4` startet an der Stelle der Meldung (`#t=Sekunden`), dazu ein direkter Link „im Video ab m:ss ansehen“ und die Untertitel der Sendung
- Hinweis auf die automatische Erstellung mit KI-Unterstützung, Links zu Datenschutz und Impressum

Die Seiten laden keine externen Skripte, Bilder, Schriften oder Stylesheets und enthalten keine Tracker. Links zu Quellen setzen `rel="noopener noreferrer"`; zusätzlich gilt `referrer: no-referrer`. Das Layout ist responsiv und folgt dem hellen oder dunklen Systemmodus.

## Ablage

```
docs/artikel/<Sendungs-ID>/<Nr>-<titel-slug>.html
docs/articles.json
```

Die Sendungs-ID entspricht der ID im Sendungsarchiv (`broadcasts.json`, UTC-Zeit `JJJJMMTTTHHMMSSZ`). `articles.json` beschreibt die Seiten der jüngsten Sendung (Titel, Pfad, Kategorie, Bereich, Video, Startzeit, Quellen-URLs) und dient späteren Startseiten-, Rubriken- und Archivfunktionen.

Artikelordner bleiben so lange erhalten wie die zugehörige Sendung in `broadcasts.json` steht. Fällt eine Sendung aus dem Archiv heraus, wird ihr Artikelordner beim nächsten Lauf entfernt, damit keine Seite auf ein gelöschtes Video zeigt. Mit dem dauerhaften Archiv (T030/T260) bleiben die Seiten entsprechend länger bestehen.

## Startseite

Die Startseite erhält unter dem Videoplayer den Block „Meldungen dieser Sendung“ mit Links auf alle Artikelseiten. Er ist statisches HTML und funktioniert auch ohne JavaScript.

## Abschalten

```json
"article_pages": {
  "enabled": true
}
```

Mit `enabled: false` entstehen keine neuen Seiten und kein Startseitenblock; vorhandene Seiten bleiben unverändert. Ohne diesen Block gilt `true`.

## Grenzen

- Gilt für die Standardsendung aus `scripts/generate.py`. Shows über `scripts/produce_show.py` erzeugen noch keine Artikelseiten.
- Die Zusammenfassung ist der Sendungstext. Bei abgeschalteter Redaktionspipeline kann dieser aus wörtlichen Sätzen der Quelle bestehen; die Kürzung auf wenige Sätze hält ihn im Rahmen kurzer Zitate.
