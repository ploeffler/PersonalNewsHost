# PersonalNewsHost

**Experimentelles, automatisiertes RSS-Nachrichtenstudio – ohne kostenpflichtige APIs oder eigenen Server.**

PersonalNewsHost liest konfigurierbare RSS-Feeds und erzeugt deutschsprachige Nachrichtenvideos. Die derzeitige **Produktivversion** veröffentlicht regelmäßig ein MP4 mit Piper-Sprachausgabe, einer Webseite und einem Video-RSS-Feed über GitHub Pages. Daneben entsteht ein **separater, noch nicht veröffentlichender Testzweig der Verarbeitung** mit Themen-Clustering, parallelen Videosegmenten und einem lippensynchronen Moderator auf Basis von MuseTalk.

> **Projektziel:** Möglichst stündlich eine automatisch erzeugte Nachrichtensendung, konfigurierbare Quellen, Moderatorenportrait und Studiokulisse, Video-RSS und **0 € monatliche Zusatzkosten**. Die Umsetzung ist ein Prototyp, kein redaktionell verifiziertes Nachrichtensystem. Die GitHub-Freikontingente und Nutzungsbedingungen müssen eingehalten werden.

## Warum dieses Projekt entstanden ist

PersonalNewsHost ist aus **zwei Motivationen** entstanden.

**1. Programmieren mit einem einfachen Prompt:** Das Projekt soll zeigen, wie man aus einer zunächst einfachen Aufgabenbeschreibung im Gespräch mit ChatGPT schrittweise ein ausführbares Programm entwickeln lassen kann. Der Ausgangspunkt war die Idee, konfigurierbare RSS-Feeds automatisch auszuwerten und daraus stündlich eine Nachrichtensendung als Video zu erzeugen. Das Programm soll **in der Cloud**, also auf fremder Recheninfrastruktur, laufen, ohne dass dafür ein eigener Server oder ein ständig geöffneter Browser nötig ist. Die besondere Herausforderung lautet: **0 € laufende Zusatzkosten**. Das ist mit frei verfügbaren Werkzeugen und kostenlosen Kontingenten grundsätzlich möglich, aber nur innerhalb ihrer jeweiligen Grenzen. Der Weg vom ersten Prompt bis zum funktionierenden Prototyp umfasst mehrere Iterationen, Tests und Korrekturen – nicht bloß einen einzigen Knopfdruck.

**2. KI als Technologie begreifbar machen:** Es gibt nicht **„die KI“** als ein einzelnes, physisches Ding. *Künstliche Intelligenz* bezeichnet eine Familie von Technologien, Modellen und Verfahren. Diese können je nach Modell und Rechenbedarf auf dem eigenen Computer zu Hause oder auf Rechnern in einem Rechenzentrum ausgeführt werden. ChatGPT dient hier als Werkzeug zur Entwicklung des Programms; das bedeutet nicht, dass jede Funktion des fertigen Programms über ChatGPT oder eine OpenAI-API laufen muss. PersonalNewsHost verbindet unterschiedliche Bausteine: klassische RSS-Verarbeitung und Videowerkzeuge ebenso wie lokal ausführbare KI-Modelle für Sprache und Lippenbewegungen.

### Kostenlos ist eine Konfiguration, keine technische Grenze

Die **kostenlose Betriebsweise** ist die Vorgabe dieses Prototyps, nicht das grundsätzliche Limit der Architektur. PersonalNewsHost soll auch mit **kostenpflichtigen Technologien und Diensten** betrieben werden können – beispielsweise für Sprachsynthese, Textanalyse, Bild- oder Videogenerierung oder leistungsfähigere Recheninfrastruktur. Dafür müssen die jeweiligen Anbieter technisch angebunden, Zugangsdaten sicher hinterlegt und ihre Preise berücksichtigt werden. **Die aktuell dokumentierten Workflows enthalten noch keine allgemein konfigurierbare Umschaltung auf solche kostenpflichtigen Anbieter.** Das ist eine geplante Erweiterungsmöglichkeit, keine bereits fertig implementierte Funktion.

## Entwicklungschronik

Die folgende Chronik zeigt, wie aus einer einfachen Idee im Dialog mit ChatGPT schrittweise ein ausführbares Cloud-Projekt wurde. Die Schritte beschreiben **Entwicklungs- und Teststände**, nicht durchgehend produktiv veröffentlichte Funktionen.

| Phase | Entwicklung | Ergebnis |
| --- | --- | --- |
| **1. Ausgangsidee (21.10.2026)** | Der erste Prompt beschreibt konfigurierbare RSS-Feeds, eine stündlich erzeugte Nachrichtensendung als Video, einen austauschbaren Hintergrund und einen fotorealistischen Moderator. | Das Grundkonzept von PersonalNewsHost entsteht. |
| **2. Rahmenbedingungen** | Die Anwendung soll ohne eigenen Server und ohne offenen Browser laufen. Als monatliches Zusatzbudget werden ausdrücklich **0 €** festgelegt; GitHub als Plattform ist erlaubt. | GitHub Actions, GitHub Pages und kostenlose lokal ausführbare Werkzeuge bilden die Basis. |
| **3. Erste funktionsfähige Version** | RSS-Meldungen werden regelbasiert zu Sprechertexten verarbeitet; FFmpeg erstellt das Video, GitHub Pages stellt es bereit. | Automatische MP4-Veröffentlichung, Webseite, Transkript und ein Video-RSS-Feed. |
| **4. Natürlichere Sprache** | Die zunächst mögliche eSpeak-Ausgabe wird durch das deutsche neuronale Piper-Modell `de_DE-thorsten-high` ergänzt. | Deutlich natürlichere Sprachausgabe ohne kostenpflichtigen Sprachdienst. |
| **5. Themenanalyse** | Ein eigenständiger Testschritt untersucht Ähnlichkeiten innerhalb eines RSS-Feeds und zwischen mehreren Feeds. | Konservative Themenkandidaten; mögliche Mehrfachmeldungen werden zur Prüfung markiert, nicht ungeprüft zusammengeführt. |
| **6. Parallele Videoproduktion** | Die Sendung wird in sieben separat erzeugbare Segmente zerlegt: Intro, fünf Nachrichten und Outro. | Ein vollständiger FFmpeg/Piper-Test wird erfolgreich zusammengesetzt. |
| **7. Sprechender Moderator** | MuseTalk 1.5 wird mit Piper getestet. Nach einem ersten Versuch mit 5 neuronalen Bildern pro Sekunde folgt ein verbesserter Versuch mit 10 FPS und Interpolation auf 25 FPS. | Die Lippenbewegungen werden im zweiten Test als deutlich besser beurteilt. |
| **8. Vollständige MuseTalk-Testsendung (22.10.2026)** | Intro und Outro werden mit MuseTalk erzeugt, die fünf Meldungen mit FFmpeg; die Segmente werden parallel gerendert und anschließend verbunden. | [GitHub-Actions-Lauf #39800872982](https://github.com/ploeffler/PersonalNewsHost/actions/runs/39800872982) schließt mit allen neun Jobs erfolgreich ab. |
| **9. Bildgestaltung und Feinschliff** | Die Sprechgeschwindigkeit wird leicht erhöht. Individuelle, lokal erzeugte Nachrichtentafeln ersetzen in den Testbeiträgen den bisherigen blauen Ersatzhintergrund. Zudem werden die GitHub Actions auf Node.js-24-kompatible Versionen aktualisiert. | Änderungen sind im Repository umgesetzt; ihre Prüfung in einer neuen vollständigen Sendung steht noch aus. |

### Was diese Chronik zeigen soll

Der Ausgangspunkt war **kein fertiges Pflichtenheft und kein von Hand programmiertes Gesamtsystem**, sondern eine Beschreibung des gewünschten Ergebnisses. Die Umsetzung entstand durch Nachfragen, Entscheidungen, Codeänderungen, automatisierte Tests und die Beurteilung der erzeugten Videos. ChatGPT unterstützte die Entwicklung; die fertigen Workflows verwenden unterschiedliche frei verfügbare Programme und Modelle und benötigen für ihren Betrieb keine dauerhafte ChatGPT-Sitzung.

**Der Null-Euro-Ansatz ist dabei eine bewusst gewählte Betriebsvariante.** Er beweist nicht, dass Rechenleistung grundsätzlich kostenlos ist: Sie wird hier innerhalb verfügbarer kostenloser Kontingente bereitgestellt. Kostenpflichtige Modelle, APIs oder Rechenumgebungen bleiben mögliche spätere Erweiterungen.

## Aktuelle Ausgaben

- [Nachrichtenseite auf GitHub Pages](https://ploeffler.github.io/PersonalNewsHost/)
- [Video-RSS-Feed](https://ploeffler.github.io/PersonalNewsHost/feed.xml)
- [Letztes Video](https://ploeffler.github.io/PersonalNewsHost/latest.mp4)
- [Transkript](https://ploeffler.github.io/PersonalNewsHost/transcript.txt)

Der produktive Workflow überschreibt die neueste Ausgabe; ein vollständiges Sendungsarchiv wird derzeit nicht geführt.

## Funktionsstand

| Funktion | Status |
| --- | --- |
| Konfigurierbare RSS-Quellen | Produktiv |
| Regelbasierte Auswahl von Meldungen | Produktiv |
| Deutsche Sprachausgabe mit Piper `de_DE-thorsten-high` | Produktiv |
| eSpeak-NG als Fallback bei fehlendem Piper-Modell | Produktiv |
| MP4, Webseite, Transkript und Video-RSS | Produktiv |
| Automatischer stündlicher GitHub-Actions-Lauf | Aktiv, best effort |
| Konfigurierbares Portrait und Hintergrund | Standbilder produktiv; Hintergrunddatei optional |
| RSS-Themenanalyse und vorsichtiges Clustering | Experimentell |
| Sieben parallele Segmente: Intro, fünf Meldungen, Outro | Experimentell |
| MuseTalk 1.5 mit Piper, 10 neuronale FPS und 25 Ausgabe-FPS | Einzeltests erfolgreich |
| MuseTalk für vollständiges Intro und Outro | Vollständiger 7-Segment-Test erfolgreich; noch nicht produktiv |
| Individuelle Nachrichtentafeln | Im Testworkflow implementiert, noch nicht neu getestet |
| Externe Nachrichtenfotos / Fremdvideos | Noch nicht implementiert |
| Redaktionelle Faktenprüfung und automatische Freigabe | Noch nicht implementiert |

**Wichtig:** Die produktive Sendung verwendet derzeit **keinen sprechenden KI-Avatar**. MuseTalk ist ausschließlich in manuell gestarteten Testworkflows aktiv. Ein erfolgreicher Testlauf bedeutet nicht automatisch, dass dessen Video öffentlich erscheint.

## Einrichtung

1. Repository auf GitHub verwenden und unter **Settings → Pages** die Veröffentlichung aus **main /docs** aktivieren.
2. Unter **Actions → Generate news video** den Produktivworkflow einmal manuell starten.
3. `config.json` anpassen: RSS-Feeds, Titel, Anzahl der Meldungen und Piper-Sprechtempo.
4. Optional eigenes Portrait unter `assets/presenter.png` und eigene Studiokulisse unter `assets/background.jpg` bereitstellen. Nur Material verwenden, für das die erforderlichen Rechte vorliegen.

Der Produktivworkflow `.github/workflows/news.yml` wird außerdem per Cron um Minute 17 jeder Stunde angefordert. GitHub garantiert weder einen exakten Startzeitpunkt noch die Ausführung jedes geplanten Laufs.

## Konfiguration

Die wesentlichen Optionen in `config.json`:

| Einstellung | Bedeutung |
| --- | --- |
| `feeds` | Liste der RSS-Adressen |
| `max_items` | Maximale Zahl der Meldungen |
| `max_description_chars` | Länge der verwendeten Feed-Kurzbeschreibung |
| `piper_length_scale` | Sprechtempo der Piper-Stimme; aktuell 1.06 (kleiner = schneller) |
| `presenter` | Portraitdatei |
| `background` | Hintergrunddatei |
| `presenter_settings` | Name, Metadaten, Portrait, Stimme und Szeneneinstellungen |

`presenter_settings.lip_sync.enabled` ist in der **Produktivkonfiguration weiterhin `false`**. Der MuseTalk-Testworkflow liest seine eigene Verarbeitungslogik; das Umstellen dieses Schalters aktiviert MuseTalk **nicht** automatisch im Produktivworkflow. Die Einstellung `gender` ist derzeit nur ein Metadatenfeld und erzeugt keine andere Stimme oder Person.

## Technische Architektur

### 1. Produktive Veröffentlichung

```text
RSS-Feeds
   ↓
scripts/generate.py
   ↓
Titel und Kurzbeschreibungen → Piper TTS → FFmpeg
   ↓
docs/latest.mp4 + docs/index.html
docs/transcript.txt + docs/feed.xml
   ↓
GitHub Pages
```

Workflow: [Generate news video](https://github.com/ploeffler/PersonalNewsHost/actions/workflows/news.yml)

### 2. Experimentelle parallele Nachrichtensendung

```text
RSS-Feeds
   ↓
scripts/analyze_topics.py
   ↓
Themenkandidaten und Quellenhinweise
   ↓
scripts/build_broadcast_plan.py
   ↓
Intro ───────── MuseTalk + Piper
Meldungen 1–5 ─ FFmpeg + Piper   (parallel)
Outro ───────── MuseTalk + Piper
   ↓
scripts/assemble_segments.py
   ↓
Testvideo als GitHub-Actions-Artefakt
(keine automatische Veröffentlichung)
```

Das Clustering verwendet eine konservative Ähnlichkeitsheuristik. Ähnliche Artikel werden **nicht** zu neuen, vermeintlich bestätigten Fakten verschmolzen: Der gesprochene Beitrag stammt jeweils aus einer führenden RSS-Meldung. Weitere ähnliche Quellen werden als Prüfkandidaten markiert.

Der Moderator erscheint im experimentellen Konzept nur in Intro und Outro. Die fünf Nachrichtenbeiträge benötigen daher keine rechenintensive Lippenanimation. Für die MuseTalk-Segmente werden **10 KI-Bilder pro Sekunde** berechnet; FFmpeg interpoliert auf **25 FPS**. Die Stimme bleibt Piper `de_DE-thorsten-high`. Der vollständige Zusammenschnitt war in Testlauf #39800872982 erfolgreich. Die neuesten Änderungen sind noch nicht getestet.

Testworkflow: [Parallel broadcast with MuseTalk](https://github.com/ploeffler/PersonalNewsHost/actions/workflows/parallel-musetalk-broadcast.yml)

## Neu: Nachrichtentafeln und Node.js 24

Der experimentelle Renderer erzeugt mit `scripts/story_card.py` und Pillow für jeden Beitrag eine individuelle Nachrichtentafel mit Schlagzeile, Quellenbezeichnung und Akzentfarbe. Diese ersetzt den bisherigen einfarbigen blauen Ersatzhintergrund. Echte Nachrichtenfotos sind weiterhin nicht integriert. Die Änderung ist noch nicht in einem vollständigen Lauf geprüft.

Die GitHub-Actions-Versionen wurden wegen der Node.js-20-Annotations auf `actions/checkout@v5`, `actions/upload-artifact@v6` und `actions/download-artifact@v7` angehoben. Auch das muss noch in einem neuen Lauf geprüft werden.

## Workflows und wichtige Dateien

| Datei | Aufgabe |
| --- | --- |
| `.github/workflows/news.yml` | Stündliche Produktivveröffentlichung |
| `.github/workflows/analyze-rss-topics.yml` | Themenanalyse testen |
| `.github/workflows/parallel-broadcast.yml` | Parallele Sendung ohne MuseTalk testen |
| `.github/workflows/musetalk-piper-10fps.yml` | Lippenanimation einzeln testen |
| `.github/workflows/parallel-musetalk-broadcast.yml` | Vollständige experimentelle Sendung |
| `scripts/generate.py` | Produktive Generierung |
| `scripts/analyze_topics.py` | RSS-Themenkandidaten |
| `scripts/build_broadcast_plan.py` | Szenen- und Sprechplan |
| `scripts/render_segment.py` | Nachrichtenbeiträge und Standbildszenen |
| `scripts/story_card.py` | Automatisch erzeugte Nachrichtentafeln |
| `scripts/render_musetalk_segment.py` | MuseTalk-Intro/-Outro mit Piper |
| `scripts/assemble_segments.py` | Zusammenfügen der Testsegmente |
| `assets/` | Moderatorenbild und optionale Kulisse |
| `docs/` | Veröffentlichte Dateien |

## Lokal testen (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
python3 -m pip install piper-tts
python3 scripts/generate.py
```

Ohne lokal vorhandenes Piper-Modell `models/de_DE-thorsten-high.onnx` greift der Produktivgenerator auf eSpeak-NG zurück. Der GitHub-Produktivworkflow versucht das Piper-Modell automatisch herunterzuladen. Die MuseTalk-Testumgebung benötigt zusätzliche große Modelle und CPU-Pakete; dafür sind die separaten Actions-Workflows vorgesehen.

## Kosten, Grenzen und Verantwortung

- **0 € ist ein Ziel unter Bedingungen, keine Kosten- oder Verfügbarkeitsgarantie.** GitHub Actions und GitHub Pages unterliegen Kontingenten, Nutzungsregeln und möglichen Änderungen. Besonders CPU-lastige MuseTalk-Tests können viel Actions-Laufzeit verbrauchen.
- Keine kostenpflichtige OpenAI-API ist in den aktuellen Workflows eingebunden. Die Texte werden regelbasiert aus RSS-Metadaten erstellt; dies ist **keine** KI-gestützte Recherche oder unabhängige Faktenprüfung.
- Automatische Übernahme fremder Fotos oder Videos ist nicht implementiert. Für Portraits, Bilder, Audio, RSS-Inhalte und verwendete Modelle sind Urheber-, Persönlichkeits- und Lizenzrechte zu prüfen.
- Keine Zugangsdaten in `config.json` oder das öffentliche Repository schreiben. RSS-Inhalte sind fremde, nicht vertrauenswürdige Eingaben.
- Für Inhalt, sachliche Richtigkeit und Veröffentlichung der Sendung bleibt der Betreiber verantwortlich.

## Roadmap

### Version 1.0 – Kostenfreier, vollständig konfigurierbarer Nachrichtenbetrieb

**Version 1.0 ist das Ziel für den vollständigen kostenlosen Ablauf:** von der RSS-Quelle bis zur automatisch veröffentlichten Nachrichtensendung einschließlich einer **Konfigurationsoberfläche im Webbrowser**. Die Version 1.0 ist noch nicht erreicht.

**Für v1.0 vorgesehen:**

1. **Produktionspipeline abschließen:** Den vollständigen MuseTalk-Workflow mit erhöhtem Sprechtempo, individuellen Nachrichtentafeln und aktualisierten GitHub Actions testen; Bild, Ton und Übergänge prüfen.
2. **Stündliche Veröffentlichung:** Die erprobte Segment-Pipeline kontrolliert in den automatischen Veröffentlichungsablauf übernehmen, inklusive MP4, Webseite, Transkript und Video-RSS.
3. **Webbasierte Konfiguration entwickeln:** RSS-Quellen hinzufügen, entfernen und bearbeiten; Sendungstitel, Anzahl der Meldungen, Stimme und Sprechtempo einstellen; Moderatorbild und Hintergrund hochladen beziehungsweise auswählen; Szenenoptionen verwalten.
4. **Konfiguration sicher speichern:** Änderungen aus der Weboberfläche nachvollziehbar in die Projektkonfiguration übernehmen. Eine mögliche Umsetzung ist eine statische Oberfläche über GitHub Pages mit autorisiertem Speichern im GitHub-Repository. Authentifizierung und Schreibberechtigungen müssen vor der Umsetzung geklärt werden; **keine Zugangstokens im öffentlichen Quellcode oder in dauerhaftem Browserspeicher ablegen**.
5. **Bedienung und Zuverlässigkeit:** Konfigurationswerte validieren, Fehlermeldungen anzeigen, eine Testsendung manuell anstoßen können und den Status des letzten Laufs sichtbar machen.
6. **Qualität und Quellen:** Themenauswahl und redaktionelle Prüfhilfen verbessern. Optional rechtlich nutzbares Nachrichtenbildmaterial ergänzen; selbst erzeugte Nachrichtentafeln bleiben als Fallback verfügbar.

**Abnahmekriterium für v1.0:** Ein Anwender kann die kostenlose Nachrichtensendung **über eine Webseite konfigurieren**, ohne `config.json` von Hand zu bearbeiten, und die konfigurierte Sendung wird über den Cloud-Workflow automatisch erzeugt und als Video sowie Video-RSS bereitgestellt – ohne eigenen dauerhaft laufenden Server oder kostenpflichtige API. Die Nutzung bleibt an kostenlose Kontingente und deren Bedingungen gebunden.

### Nach Version 1.0 – Optionale Erweiterungen

- Austauschbare kostenpflichtige oder selbst gehostete Dienste für Recherche, Sprachsynthese, Bild- und Videogenerierung sowie Rechenleistung.
- Zusätzliche Bild- und Videoquellen, Sendungslayouts, Moderatoren und Stimmen.
- Erweiterte redaktionelle Prüf- und Freigabeprozesse.

Die kostenfreie Konfiguration bleibt dabei ein eigenständiger, ohne Bezahlangebote nutzbarer Betriebsmodus.

