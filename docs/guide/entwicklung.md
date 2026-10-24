# entwicklung

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


## Neu: Nachrichtentafeln und Node.js 24

Der experimentelle Renderer erzeugt mit `scripts/story_card.py` und Pillow für jeden Beitrag eine individuelle Nachrichtentafel mit Schlagzeile, Quellenbezeichnung und Akzentfarbe. Diese ersetzt den bisherigen einfarbigen blauen Ersatzhintergrund. Echte Nachrichtenfotos sind weiterhin nicht integriert. Die Änderung ist noch nicht in einem vollständigen Lauf geprüft.

Die GitHub-Actions-Versionen wurden wegen der Node.js-20-Annotations auf `actions/checkout@v5`, `actions/upload-artifact@v6` und `actions/download-artifact@v7` angehoben. Auch das muss noch in einem neuen Lauf geprüft werden.


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


