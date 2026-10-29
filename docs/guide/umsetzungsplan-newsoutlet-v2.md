# Aufgabenanalyse und Umsetzungspakete

Stand: 29.10.2026 · Branch `Full-featured-Newsoutlet` · untersuchter Basiscommit `6b97cb9`.

Die ursprüngliche Vorlage umfasst **75 Aufgaben in 16 Epics**. Mit der Nutzerergänzung zum Linux-/Docker-Betrieb umfasst der Gesamtplan **140 Aufgaben in 32 Epics**, aufgeteilt in **44 Arbeitspakete**. Die Vorlage bleibt unverändert. Ihre Anweisungen werden als Anforderungen des Aufgabenplans ausgewertet; sie werden durch diese Analyse nicht automatisch ausgeführt. Kein Implementierungsstatus wird auf „done“ gesetzt.

## Ausgangslage und Grenzen der Analyse

Der Branch wurde vom lokal verfügbaren `main` erstellt. Eine Übereinstimmung mit dem aktuellen GitHub-Stand wurde nicht geprüft. Der andere Checkout `source/` enthält zahlreiche zusätzliche, uncommittete Änderungen; sie gehören nicht zur Basis dieses Plans und dürfen nicht stillschweigend übernommen werden.

Eine erste Sichtung zeigt Wiederverwendungspotenzial:

- `scripts/provider_registry.py`: Verträge, Registry und Planung von Budgets/Verarbeitungsorten; laut Modulbeschreibung keine Ausführung externer Aufrufe. Ausgangspunkt für T100/T101, kein Nachweis ihrer vollständigen Erfüllung.
- `scripts/build_broadcast_plan.py`: deterministischer Produktionsplan mit Review-Hinweisen. Ähnliche Quellen werden ausdrücklich nicht als faktisch zusammengeführt behandelt. Ausgangspunkt für T012/T113/T151.
- `scripts/render_segment.py`, `scripts/assemble_segments.py`, `scripts/render_musetalk_segment.py`: bestehende Ansatzpunkte für Segmentproduktion und Avatar-Experimente; Produktivreife ist noch zu prüfen.
- `scripts/lipsync.py`: ausdrücklich amplitudengetriebene Mundanimation, keine phonemgenaue Synchronisation. T162 ist dadurch nicht erledigt.
- Vorhandene Tests unter anderem für Registry und Sendungsplanung sollen erweitert werden.

Dies ist eine Aufgaben- und Abhängigkeitsanalyse mit gezielter Codesichtung, keine vollständige Bestandsaufnahme T001, kein Testlauf und keine aktuelle Anbieter- oder Rechtsprüfung.

## Empfohlene Lieferstufen

1. **Basis:** A00–A02. Bestandsabgleich, Schema, CI, sichere Provider-Verträge und Mocks.
2. **Erstes nutzbares Nachrichtenportal:** A03–A07 und A09 sowie T040 aus A08. Zwei Shows, Kategorien, Artikel, Quellen, sichere Veröffentlichung, Navigation, Archiv, Suche und kompatible Feeds; keine bezahlten Dienste erforderlich.
3. **Weitere Kanäle:** Rest von A08. Podcast, Telegram-Erweiterung und statischer Newsletter.
4. **Redaktion und nachvollziehbare Prüfungen:** A10–A13. Rollen, Belege, Routing, Korrekturen und quellengebundene Texte.
5. **Erweiterte Produktion:** A14. Formate, Rundown und Mehrstimmendialoge.
6. **Optionale Medien:** A15–A16. Externe Clips und realistische Avatare nach technischer Evaluierung und Anbieterentscheidung.
7. **Gesamtabnahme:** A17. Dokumentation und Tests entstehen zusätzlich in jedem einzelnen Paket.

Die Reihenfolge der Pakete ist eine Empfehlung, keine Freigabe zum Übergehen von Aufgabenabhängigkeiten. Innerhalb eines Pakets sind die Originalabhängigkeiten einzuhalten. Unabhängige Teile können getrennte Änderungen bilden; ein Paket ist nicht automatisch ein einzelner großer PR.

## Lücken und notwendige Präzisierungen

Der Originalgraph hat keine fehlenden Aufgabenreferenzen und keinen Zyklus. Fachliche Voraussetzungen sind jedoch teilweise nur im Text genannt:

| Aufgabe | Empfohlene Präzisierung |
|---|---|
| T120 | T135 als Voraussetzung ergänzen: Claim-Extraktion darf Schutzmaßnahmen nicht umgehen. |
| T115 | T125 und bei generierten Kommentaren T133/T134 vor produktiver Freigabe abschließen. |
| T122 | T102 bzw. die Prüfung der jeweiligen Datenquelle vor realer Anbindung abschließen. |
| T125 | T132 vor Aktivierung der kritischen Zweitmeinung abschließen. T132 liefert Ergebnisse; T125 entscheidet das Routing. So entsteht keine Rückkopplung im Aufgabengraphen. |
| T131 | Claim-Vertrag aus T120 vor quellenreferenzierter Generierung bereitstellen; T133/T134 vor Veröffentlichung generierter Texte abschließen. |
| T032 | T022 für die vollständige Sitemap berücksichtigen. |
| T040 | T020 für den Artikel-Feed berücksichtigen. |
| T144, T166 | T103 für die jeweils verlangte Cache-Nutzung berücksichtigen. |
| T143 | T142, T144 und T145 als Freigabebedingungen für externe Clips berücksichtigen. |
| T152 | T125/T133 sowie T162/T167 vor Veröffentlichung eines geprüften Avatar-Berichts berücksichtigen. |
| T153 | T125/T133 als Freigabebedingungen für faktengestützte Dialoge berücksichtigen. |
| T081 | Nicht nur den heutigen Vorgängergraphen prüfen: alle 75 Aufgaben brauchen eine Abnahme oder eine dokumentierte Zurückstellung. |

Diese Ergänzungen sind Vorschläge und wurden nicht heimlich in die Original-YAML eingetragen. T072 und T080 sind Querschnittsaufgaben: CI und Dokumentation müssen laufend gepflegt werden, auch wenn ihre abschließende Abnahme später erfolgt.

## Entscheidungen ohne unnötige Blockade

- **D1 Anbieter:** Verträge, Mocks und Benchmark-Gerüst sind vorab möglich. Aktuelle Preise, Bedingungen und Datenschutz werden erst bei der Anbieterbewertung recherchiert; dieser Plan empfiehlt keinen konkreten Dienst.
- **D2 Budget:** Budgetwächter mit Standard 0 implementieren. Eine positive Ausgabengrenze und Aktivierung realer Dienste bleiben eine separate Entscheidung. T101 muss deshalb nicht vollständig warten.
- **D3 Avatar-Technik:** Evaluation und Mockadapter sind vorab möglich. Fotorealistische Produktionsqualität ist ein gesonderter Nachweis.
- **D4 Stimmen:** Standardstimmen und Fallback sind vorab möglich. Stimmklonen gehört nicht zur ersten Lieferstufe.
- **D5 Freigabe:** Alle Routing-Zustände implementieren; die produktive Schwellen- und Freigabepolitik vor Aktivierung festlegen. Bis dahin keine automatische Freigabe unsicherer Fälle.

## Technische Risiken und kleinere Teilaufgaben

1. **Datenvertrag zuerst:** Stabile IDs für Artikel, Claims, Shows, Sendungen und Medien; Schema-Version, Quellenfundstelle, Zeitstempel und Korrekturhistorie. Das verhindert unterschiedliche Datenmodelle für Web, Video und Redaktion.
2. **Budget und Wiederaufnahme:** T101/T103/T140 jeweils in Speichervertrag, Zustandsübergänge, Ausführung und Ausfalltests zerlegen. Kosten vor Aufruf reservieren; konkurrierende Läufe und doppelte Jobzustellung prüfen. Ein einfacher Zähler nach erfolgreicher Antwort reicht nicht.
3. **Veröffentlichung:** T051/T030 in Erstellung, Validierung, Umschaltung und Aufräumen zerlegen. Erst finale Videos archivieren und validieren, dann veröffentlichen. Nur temporäre Medien und Caches bereinigen; Archivvideos bleiben erhalten.
4. **Redaktion:** T111/T125/T128 in Zustandsmodell, Entscheidung, Persistenz, Wiederaufnahme und Bedienweg zerlegen. Menschliche Freigaben benötigen autorisierte Akteure, nachvollziehbare Ereignisse und Schutz vor doppelter Verarbeitung.
5. **Belegprüfung:** Quellenübereinstimmung ist kein Wahrheitsbeweis. Testkorpus nach Themen trennen; Erwartungswerte und Fehlalarmgrenzen vor Implementierung festlegen. T129-Fixtures früh anlegen, Endabnahme nach T125.
6. **Textschutz:** Entfernen vermeintlicher Anweisungen allein schützt nicht zuverlässig vor Prompt Injection. T135 braucht getrennte Datenfelder, erlaubte Ausgaben und keine aus Modellantworten abgeleiteten Aktionen. Ähnlichkeitswerte aus T134 ersetzen keine Lizenzprüfung.
7. **Medienqualität:** T142/T165/T168 brauchen feste Referenzclips, Messverfahren und Kriterien für menschliche Sichtung. Automatische Erkennung realer Personen oder sämtlicher Artefakte ist keine garantierte Fähigkeit.
8. **Messbare Abnahme:** Für T063 eine feste Audiostichprobe und Messregel; für T113/T151 konkrete Zeittoleranzen; für T129 getrennte Mindestwerte; für T165 eine Bewertungsrubrik definieren. Unbestimmte Formulierungen wie „natürlich“ sind sonst nicht abnehmbar.
9. **Kein einheitlicher Aufwand pro ID:** Schema und kleine Feed-Erweiterungen sind anders zu planen als externe Jobs oder realistische Avatare. Belastbare Zeitschätzungen erst nach A00 und technischen Prototypen; keine erfundenen Tagesangaben.

## Pakete und konkrete Zerlegung

Jede Originalaufgabe wird bei Umsetzung in drei überprüfbare Änderungen zerlegt: **(a) Vertrag/Konfiguration und Fixture, (b) Implementierung plus Pipeline-Anbindung, (c) relevante Tests, Dokumentation und Abnahmenachweis**. Große Aufgaben erhalten die oben genannten zusätzlichen Teilschritte. Ein Task gilt erst als abgeschlossen, wenn seine ursprünglichen Akzeptanzkriterien erfüllt sind.

### A00 – Bestand und Schnittstellen

Aufgaben: T001. Lieferbereich: Basis.

Zerlegung: Skripte, Konfiguration, Workflows und Tests inventarisieren; vorhandene Implementierungen den 75 Aufgaben zuordnen; Datenmodell und Migrationsgrenzen festhalten.

Paketabnahme: Inventar mit belegten Dateipfaden; offene PRs separat prüfen; kein bestehender Prototyp gilt ohne Abnahme als fertig.

- **T001: Code- und Workflow-Inventar erstellen** — ursprüngliche Vorgänger: keine.

### A01 – Schema, CI und Sicherheit

Aufgaben: T002, T072, T073. Lieferbereich: Basis.

Zerlegung: Schema und Validator entwickeln; alte Konfiguration als Fixture sichern; Validierung, Tests, Linkprüfung und Geheimnisscan in CI integrieren.

Paketabnahme: Ungültige Konfiguration stoppt vor Produktion; Regressionstests laufen mit lokalen Fixtures.

- **T002: Konfigurationsschema einfuehren** — ursprüngliche Vorgänger: T001.
- **T072: Testabdeckung und CI** — ursprüngliche Vorgänger: T002.
- **T073: Datenschutz und Sicherheit** — ursprüngliche Vorgänger: T002.

### A02 – Provider-Grundlage ohne externe Aufrufe

Aufgaben: T100, T101, T103, T104, T130, T135. Lieferbereich: Basis.

Zerlegung: Bestehende Registry erweitern; typisierte Verträge und deterministische Mocks; Budgetreservierung und dauerhafte Verbrauchsbuchung; Cache, Allowlist und strikte Antwortvalidierung.

Paketabnahme: Budget 0 verhindert bezahlte Aufrufe; Timeout, Wiederholung und Fallback getestet; parallele Läufe können das Budget nicht doppelt ausgeben.

- **T100: Provider-Interface, Registry und Mock-Provider** — ursprüngliche Vorgänger: T002.
- **T101: Budget- und Quota-Waechter** — ursprüngliche Vorgänger: T100.
- **T103: Ergebnis-Cache und Idempotenz** — ursprüngliche Vorgänger: T100.
- **T104: Datenabfluss-Filter und Protokoll** — ursprüngliche Vorgänger: T100.
- **T130: Analyse-Aufgaben und Ausgabeschemata** — ursprüngliche Vorgänger: T100.
- **T135: Prompt-Injection-Schutz fuer Feed-Inhalte** — ursprüngliche Vorgänger: T100.

### A03 – Shows und Nachrichtenauswahl

Aufgaben: T010, T011, T012, T052. Lieferbereich: Kernprodukt.

Zerlegung: Alte Konfiguration auf Standardshow abbilden; Ausgaben nach Show trennen; Kategorien, Quellenregeln und deterministisches Clustering ergänzen.

Paketabnahme: Zwei getrennte Shows; alte Konfiguration bleibt kompatibel; Cluster erhalten sämtliche Quellen und verwechseln Ähnlichkeit nicht mit Bestätigung.

- **T010: Mehrere Sendungsformate (Editionen) unterstuetzen** — ursprüngliche Vorgänger: T002.
- **T011: Rubriken und Themenzuordnung** — ursprüngliche Vorgänger: T010.
- **T012: Duplikat- und Themenclustering** — ursprüngliche Vorgänger: T011.
- **T052: Quellen-Blockliste und Gewichtung** — ursprüngliche Vorgänger: T011.

### A04 – Veröffentlichung und Betrieb absichern

Aufgaben: T051, T070, T071. Lieferbereich: Kernprodukt.

Zerlegung: Vorprüfung und temporäres Ausgabeziel; erst vollständig geprüfte Artefakte veröffentlichen; Feed-Fallbacks, Zeitlimits und Show-Concurrency ergänzen.

Paketabnahme: Fehler lässt letzte gute Sendung bestehen; einzelne Feed-Ausfälle sind beherrscht; Laufzeitverbrauch ist gemessen und dokumentiert.

- **T051: Qualitaetspruefungen vor Veroeffentlichung** — ursprüngliche Vorgänger: T012.
- **T070: Planung und Laufzeitbudget in Workflows** — ursprüngliche Vorgänger: T010.
- **T071: Fehlerbehandlung, Wiederholung und Benachrichtigung** — ursprüngliche Vorgänger: T051.

### A05 – Artikel und Herkunftsnachweise

Aufgaben: T020, T050, T062, T124. Lieferbereich: Kernprodukt.

Zerlegung: Stabile Artikel-IDs und URLs; sichere HTML-Ausgabe; Quellen, Abrufzeit, Bildnachweise und KI-Kennzeichnung im gemeinsamen Datenmodell.

Paketabnahme: Jeder Beitrag besitzt verlinkte Quellen; unbekannte Bildherkunft wird markiert; Feed-HTML und URLs sind validiert.

- **T020: Statische Artikelseiten pro Meldung** — ursprüngliche Vorgänger: T011.
- **T050: Quellentransparenz und Kennzeichnung KI-generierter Inhalte** — ursprüngliche Vorgänger: T020.
- **T062: Bildquellen und Lizenzen** — ursprüngliche Vorgänger: T020.
- **T124: Bild- und Medienherkunft pruefen** — ursprüngliche Vorgänger: T062.

### A06 – Eilmeldungen und Webnavigation

Aufgaben: T013, T021, T022, T032. Lieferbereich: Kernprodukt.

Zerlegung: Eilmeldungserkennung zuerst ohne Renderkosten; Kurzclip und deduplizierte Veröffentlichung; Startseite, Kategorien, Shows und Metadaten generieren.

Paketabnahme: Ohne Treffer kein Clip; Navigation und Sitemap vollständig; Barrierefreiheit geprüft; alte Feed- und Video-URLs erhalten.

- **T013: Eilmeldungs-Modus (Breaking News)** — ursprüngliche Vorgänger: T010, T012.
- **T021: Startseite im Redaktionslayout** — ursprüngliche Vorgänger: T020, T013.
- **T022: Rubrikenseiten und Sendungsseiten** — ursprüngliche Vorgänger: T021, T010.
- **T032: Sitemap, Metadaten und Teilen** — ursprüngliche Vorgänger: T020.

### A07 – Archiv und Suche

Aufgaben: T030, T031. Lieferbereich: Kernprodukt.

Zerlegung: Sendungs- und Artikelindizes versionieren; verpflichtendes Videoarchiv nach T260; Suchindex mit Größenlimit und Archivseiten erstellen.

Paketabnahme: Archivvideos bleiben erhalten; nur temporäre Dateien und Caches werden bereinigt; Suche funktioniert lokal im Browser.

- **T030: Archiv mit Aufbewahrungsregeln** — ursprüngliche Vorgänger: T020.
- **T031: Clientseitige Volltextsuche** — ursprüngliche Vorgänger: T030.

### A08 – Feeds und weitere Ausgabekanäle

Aufgaben: T040, T041, T042, T043. Lieferbereich: Ausbau.

Zerlegung: Show-/Rubrikenfeeds und Artikel-Feeds; Audio plus Kapitel; Telegram-Zuordnung; wöchentliche HTML-/Textausgabe ohne Standardversand.

Paketabnahme: Bestehender Gesamtfeed kompatibel; gültige Enclosures und Links; fehlende Telegram-Secrets führen zum Überspringen.

- **T040: Feeds pro Show und Rubrik** — ursprüngliche Vorgänger: T010, T011.
- **T041: Audio-Podcast-Feed** — ursprüngliche Vorgänger: T040.
- **T042: Telegram erweitern (optional, abschaltbar)** — ursprüngliche Vorgänger: T040.
- **T043: Woechentlicher Newsletter als statische Datei** — ursprüngliche Vorgänger: T030, T040.

### A09 – Präsentation und Untertitel

Aufgaben: T060, T061, T063. Lieferbereich: Kernprodukt.

Zerlegung: Host-/Studio-Zuordnung von Avatar-Technik trennen; Grafiktemplates vereinheitlichen; SRT-Zeiten messen und WebVTT ergänzen.

Paketabnahme: Shows unterscheiden sich sichtbar; Quellen stehen im Bild; definierte Audiostichprobe erfüllt das Untertitelziel.

- **T060: Mehrere Moderatoren und Studio-Varianten** — ursprüngliche Vorgänger: T010.
- **T061: Grafikbausteine (Einblendungen)** — ursprüngliche Vorgänger: T011.
- **T063: Untertitel verbessern** — ursprüngliche Vorgänger: T001.

### A10 – Virtuelle Redaktion und Planung

Aufgaben: T110, T111, T112, T113, T114. Lieferbereich: Redaktion.

Zerlegung: Rollenmodell und Rechte; persistenter Zustandsautomat mit begrenzten Korrekturschleifen; versionierte Prompts; Sendeplan und öffentliches Redaktionsprotokoll.

Paketabnahme: Fixture durchläuft alle Stufen; Wiederaufnahme erzeugt keine doppelte Produktion; KI-Rollen sind klar gekennzeichnet.

- **T110: Redaktionsmodell - Abteilungen und virtuelle Mitarbeiter** — ursprüngliche Vorgänger: T002, T011, T100.
- **T111: Redaktionsworkflow als Zustandsautomat** — ursprüngliche Vorgänger: T110, T012.
- **T112: Rollen-Prompts und Stilhandbuch** — ursprüngliche Vorgänger: T110.
- **T113: Redaktionskonferenz und Sendungsplanung** — ursprüngliche Vorgänger: T111, T010.
- **T114: Redaktionsprotokoll und Seite "Unsere Redaktion"** — ursprüngliche Vorgänger: T111, T050.

### A11 – Anbieterprüfung und Beleggewinnung

Aufgaben: T102, T120, T121, T122, T123. Lieferbereich: Redaktion.

Zerlegung: Anbieterrecherche und Benchmark zunächst mit Mocks vorbereiten; Claim-Schema, unabhängige Quellen, Fact-Check-Hinweise und Primärquellenvergleich implementieren.

Paketabnahme: Claims haben Fundstellen und datierte Belege; Agenturkopien zählen nicht mehrfach; reale Anbieter erst nach dokumentierter Prüfung aktivieren.

- **T102: Anbieter-Bewertung und Dokumentation** — ursprüngliche Vorgänger: T100.
- **T120: Claim-Extraktion** — ursprüngliche Vorgänger: T111.
- **T121: Mehrquellen-Abgleich** — ursprüngliche Vorgänger: T120, T012.
- **T122: Externe Fact-Check-Quellen anbinden** — ursprüngliche Vorgänger: T120, T100.
- **T123: Primaerquellen-, Zahlen- und Zitatpruefung** — ursprüngliche Vorgänger: T120.

### A12 – Bewertung, Freigabe und Korrekturen

Aufgaben: T132, T125, T126, T127, T128, T129. Lieferbereich: Redaktion.

Zerlegung: Zweitmeinung als separaten Ergebnisdienst; regelbasiertes Routing; versionierte Korrekturen; Prüfstatusanzeige und menschliche Freigabe mit Frist; Testkorpus aufbauen.

Paketabnahme: Unbelegte Meldungen erhalten keine vorgetäuschte Bestätigung; Widersprüche werden eskaliert; Fristablauf und Korrekturen sind reproduzierbar getestet.

- **T132: Mehr-Anbieter-Strategie und zweite Meinung** — ursprüngliche Vorgänger: T130, T101, T102.
- **T125: Verdikt-Modell, Schwellen und Veroeffentlichungs-Gate** — ursprüngliche Vorgänger: T121, T122, T123.
- **T126: Korrekturen und Updates** — ursprüngliche Vorgänger: T114, T125.
- **T127: Fact-Check-Anzeige in Web und Video** — ursprüngliche Vorgänger: T125, T020.
- **T128: Menschliche Freigabe bei unsicheren Meldungen** — ursprüngliche Vorgänger: T125, T071.
- **T129: Fact-Check-Testkorpus und Metriken** — ursprüngliche Vorgänger: T125.

### A13 – Texterstellung und Analyseformate

Aufgaben: T131, T133, T134, T115. Lieferbereich: Redaktion.

Zerlegung: Sprecher-, Web- und Kurztexte; Satz-zu-Quelle-Zuordnung; Zahlen-/Namensprüfung; Übernahmegrenzen; separate Analyse- und Kommentarstrecke.

Paketabnahme: Erfundene Testaussagen werden verworfen; lokale Textbildung bleibt verfügbar; Kommentar und Nachricht sind sichtbar getrennt.

- **T131: Nachrichtenformulierung (Sprechertext, Webtext, Kurzfassung)** — ursprüngliche Vorgänger: T112, T130, T135.
- **T133: Grounding-Pruefung gegen Halluzinationen** — ursprüngliche Vorgänger: T131, T120.
- **T134: Urheberrechts- und Originalitaetsschutz** — ursprüngliche Vorgänger: T131.
- **T115: Getrennte Kommentar- und Analyseabteilung** — ursprüngliche Vorgänger: T111.

### A14 – Formate und Segmentproduktion

Aufgaben: T150, T151, T153. Lieferbereich: Ausbau.

Zerlegung: Drei einfache Formate zuerst; Sendeplan in zeitlichen Rundown überführen; Segmente einzeln rendern und zusammensetzen; danach Mehrstimmendialog.

Paketabnahme: Rundown-Zeiten stimmen mit Ausgabe überein; Segmentcache wiederverwendbar; jede dargestellte Position besitzt Quellenbezug.

- **T150: Show-Format-Katalog** — ursprüngliche Vorgänger: T010.
- **T151: Segment-Engine und Rundown** — ursprüngliche Vorgänger: T150, T113.
- **T153: Roundtable- und Diskussionsformat** — ursprüngliche Vorgänger: T151, T131, T134.

### A15 – Optionale externe Videoclips

Aufgaben: T140, T141, T142, T143, T144, T145. Lieferbereich: Optional.

Zerlegung: Job-Zustandsmodell mit Submit/Poll/Download und Wiederaufnahme; Shotliste; technische Prüfung und Sichtung; Schnitt, Sekundenlimit und Kennzeichnung.

Paketabnahme: Mockjob und Timeout-Fallback funktionieren; Kostenlimit verhindert neue Jobs; jeder generierte Clip bleibt als Symbolbild gekennzeichnet.

- **T140: Video-Provider-Adapter mit asynchronen Jobs** — ursprüngliche Vorgänger: T100.
- **T141: Szenenplanung und Shot-Liste** — ursprüngliche Vorgänger: T111, T140.
- **T142: Qualitaets- und Sicherheitspruefung generierter Clips** — ursprüngliche Vorgänger: T140.
- **T143: Schnitt und Komposition externer Clips** — ursprüngliche Vorgänger: T141, T061.
- **T144: Kosten- und Zeitsteuerung fuer Videojobs** — ursprüngliche Vorgänger: T101, T140.
- **T145: Kennzeichnung von KI-Videomaterial** — ursprüngliche Vorgänger: T140, T050.

### A16 – Avatare, Stimmen und Korrespondenten

Aufgaben: T160, T161, T163, T164, T162, T165, T166, T167, T168, T152. Lieferbereich: Optional.

Zerlegung: Technikvergleich vor Anbieterwahl; fiktive Identitäten und Standardstimmen; Mockadapter; audiogetriebenes Rendering; Synchronitätsmessung; Studiointegration und Korrespondentensegment.

Paketabnahme: Reales Rendering separat bewerten; Mock-Erfolg beweist keine fotorealistische Qualität; Kennzeichnung, Budgetlimit und statischer Fallback in jeder Ausgabestrecke.

- **T160: Avatar-Anforderungen und Technologie-Evaluierung** — ursprüngliche Vorgänger: T100, T102.
- **T161: Avatar-Provider-Adapter** — ursprüngliche Vorgänger: T160, T140.
- **T163: Natuerliche deutsche Stimmen** — ursprüngliche Vorgänger: T100.
- **T164: Fiktive Host-Identitaeten** — ursprüngliche Vorgänger: T110, T160.
- **T162: Echtes Lipsync (audiogetrieben)** — ursprüngliche Vorgänger: T161, T163.
- **T165: Natuerlichkeit und Studio-Integration** — ursprüngliche Vorgänger: T162.
- **T166: Render-Strategie, Cache und Kosten** — ursprüngliche Vorgänger: T101, T161.
- **T167: Kennzeichnung und Ethik-Richtlinie synthetischer Moderatoren** — ursprüngliche Vorgänger: T161.
- **T168: Automatische Qualitaetskontrolle von Avatar und Lipsync** — ursprüngliche Vorgänger: T162.
- **T152: Korrespondenten-Segment (Schalte)** — ursprüngliche Vorgänger: T151, T164.

### A17 – Migration und Gesamtabnahme

Aufgaben: T080, T081. Lieferbereich: Abschluss.

Zerlegung: Begleitende Dokumentation konsolidieren; Fork-Migration; Ende-zu-Ende-Läufe mit zwei Shows, Mocks und erzwungenen Fehlern; optional reale Anbieter gesondert abnehmen.

Paketabnahme: Abnahmebericht nennt für jede Aufgabe erfüllt, offen oder begründet zurückgestellt; bestehende Produktionsfunktionen bleiben erhalten.

- **T080: Dokumentation aktualisieren** — ursprüngliche Vorgänger: T010, T020, T030, T040, T050, T060, T070, T102, T114, T125, T132, T144, T167.
- **T081: Abnahmelauf Ende-zu-Ende** — ursprüngliche Vorgänger: T080, T072, T114, T129, T133, T145, T168.

## Nächster konkreter Schritt

A00 beginnen: bestehende Funktionen und offene Änderungen gegen jede Anforderung abgleichen. Danach A01 in kleinen Änderungen umsetzen. Providerkosten bleiben bei 0; externe Dienste und Veröffentlichung werden durch diesen Plan nicht aktiviert.

Die maschinenlesbare Zuordnung steht in `../../planning/arbeitspakete.yaml`. Sie enthält zusätzlich die topologischen Ebenen des unveränderten Originalgraphen; diese Ebenen sind keine Aufwandsschätzung.

## Ergänzung: Linux-Dienst und Docker als gleichwertige Betriebswege

Nutzeranforderung vom 29.10.2026: Installation aus dem Repository auf Linux mit Start-/Stop-Skripten oder alternativer Betrieb im Docker-Container; Containerinstallation per CLI und Portainer dokumentieren.

Diese Anforderungen sind Bestandteil des geplanten Produkts. GitHub Actions und Pages sind damit keine zwingende Laufzeitvoraussetzung mehr. Der lokale Dienst benötigt eine Zeitplanung und muss die erzeugte Website sowie Medien lokal über HTTP ausliefern können. Beide Installationswege verwenden denselben Anwendungskern und dieselben Konfigurationsregeln.

| Paket | Aufgaben | Ergebnis |
|---|---|---|
| A18 | T180–T182 | Betriebsvertrag, Linux-Installation, start.sh/stop.sh/status.sh und systemd-Integration |
| A19 | T183–T185 | Dockerfile und Compose, CLI-Installationsanleitung, getesteter Portainer-Stack und Anleitung |
| A20 | T186–T187 | Persistente Zustände, Backup/Restore, Updates und Abnahme aller Installationsvarianten |

T180 gehört unmittelbar nach der Bestandsaufnahme in die Architekturplanung. A18 und A19 werden vor der ersten produktiven lokalen Auslieferung umgesetzt; sie warten nicht auf optionale Avatare. T186 wird mit Budget-/Jobzuständen und Archiv integriert. T187 ist zusätzlich zu T081 Voraussetzung für die endgültige Gesamtabnahme; diese ergänzende Freigabebedingung verändert den Originalgraphen nicht.

Die acht Aufgaben sind in `../../planning/betriebswege-ergaenzung.yaml` mit Abhängigkeiten und Akzeptanzkriterien ausgeführt. Insbesondere werden sichere wiederholte Starts/Stops, Wiederaufnahme, Zeitzone, lokale Ports, Mounts und Dateirechte, fehlende Secrets sowie der Erhalt der Daten bei Container-Neuerstellung geprüft.

**Anpassung der bisherigen Rahmenbedingungen:** C2 wird für lokale Installationen um zugriffsgeschützte Laufzeit-Secrets bzw. Secret-Mounts ergänzt. GitHub Secrets bleiben für Actions vorgesehen. C7 wird um lokale Speicher- und Ressourcenbudgets ergänzt. Es gibt keine Zugangsdaten im Repository oder im Container-Image.

Für Portainer ist die Verfügbarkeit des Images explizit zu dokumentieren: zunächst lokaler Build auf dem Zielhost plus Stack-Deployment mit diesem Image. Eine Registry-URL wird erst angegeben, wenn eine Veröffentlichung eingerichtet ist. Die tatsächlichen CLI-/Portainer-Anleitungen entstehen und werden geprüft, sobald die entsprechenden Installationsartefakte implementiert sind; dieser Plan behauptet noch keine funktionierende Containerinstallation.

## Ergänzung: Passwortgeschützte Konfiguration

Nutzeranforderung: Der Docker-Container erhält den Admin-Benutzernamen und einen Passwort-Hash über Umgebungsvariablen. Die Konfigurationsseite wird mit diesem Zugang geschützt. Ohne Vorgaben gilt ausdrücklich **admin/admin**.

**A21 (T188–T190)** ergänzt Laufzeitkonfiguration, serverseitige Authentifizierung und geprüfte Dokumentation:

| Variable | Bedeutung | Verhalten ohne Vorgabe |
|---|---|---|
| `ADMIN_USER` | Admin-Benutzername | `admin` |
| `ADMIN_PASSWORD_HASH` | Argon2id-Passwort-Hash im PHC-Format | Mitgelieferter Hash für Passwort `admin` |

Ein individuell gesetzter Hash ersetzt den Standardzugang. Leere explizite Werte oder ungültige Hashes verursachen einen Konfigurationsfehler statt eines Rückfalls auf das Standardpasswort. Ein CLI-Helfer erzeugt passende Hashes mit verdeckter Passworteingabe. Die Variablen gelten auch für den direkten Linux-Dienst.

Der Schutz liegt im HTTP-Dienst: Anmeldung, serverseitige Sitzung, Logout, Sitzungsablauf, CSRF-Schutz für Änderungen und Begrenzung von Anmeldeversuchen. Nicht nur die sichtbare Seite, sondern auch Konfigurationsabrufe, Speichern und direkte Dateipfade werden geschützt. Individuelle Hashes werden weder öffentlich ausgeliefert noch geloggt. Öffentliche Nachrichten bleiben frei zugänglich.

Bestehende statische Konfigurationsdateien und `settings.html` müssen auf Umgehungen geprüft werden. Auf einer reinen GitHub-Pages-Ausgabe wird die administrative Konfigurationsseite nicht ausgeliefert, da der vorgesehene Schutz einen Server benötigt. Die Verwaltung erfolgt über den Linux-/Containerdienst.

CLI-, Compose- und Portainer-Anleitungen müssen die unveränderte Übergabe von PHC-Hashes einschließlich ihrer Dollarzeichen jeweils testen. Hashänderungen greifen spätestens nach Neustart; bestehende Sitzungen werden dabei ungültig. T190 ist eine zusätzliche Freigabebedingung für T187 und T081. Das ist eine geplante Anforderung, noch keine implementierte Zugangssicherung.

## Ergänzung: Social-Media-Ausgaben

Die Ausgabe wird um plattformgerechte Exportpakete und optional aktivierbare Publisher erweitert. Priorität 1: **YouTube inklusive Shorts, Instagram, Facebook inklusive Reels und TikTok**. Danach folgen WhatsApp, LinkedIn, X, Threads, Bluesky und Mastodon; zusätzliche Exportziele sind Snapchat, Pinterest und Reddit. Telegram bleibt über T042 integriert.

Die Auswahl der großen Reichweitenplattformen orientiert sich am [DataReportal-Bericht zur Jahresmitte 2026](https://datareportal.com/reports/digital-2026-mid-year-global-update-report). Die weiteren Ziele ergänzen die Nachrichtenverteilung und sind keine behauptete Reichweitenrangliste. Konkrete Formatgrenzen und Posting-Zugänge sind erst anhand aktueller offizieller Dokumentation zu prüfen.

| Paket | Aufgaben | Ergebnis |
|---|---|---|
| A22 | T200–T202 | Konfigurierbare Profile, Videos in Quer-/Hochkant-/Quadratformat, Bilder, Untertitel, Texte und Exportpakete |
| A23 | T203–T204 | Geprüfte optionale Publisher, Kontoverbindung, Freigaben und persistente Warteschlange |
| A24 | T205–T206 | Korrekturen, Kennzeichnung, Dokumentation und Abnahme |

Export ist unabhängig von API-Konten möglich. Automatisches Posten ist standardmäßig aus und wird je Plattform separat eingerichtet. Der Umfang der realen Publisher hängt von tatsächlich verfügbaren offiziellen Schnittstellen, Freigaben und Kosten ab; insbesondere wird keine automatische Veröffentlichung in WhatsApp-Kanäle vorausgesetzt. Es werden durch die Planung keine Konten verbunden oder Posts verschickt.

Pro Export gehören Video/Bild, passender Text, Quellenlink, Untertitel, Vorschaubild und ein Manifest zusammen. Reframing und sichere Textbereiche erhalten Quellen und Kennzeichnungen auch im Hochkantformat. Die Adminoberfläche bietet Vorschau und Download sowie später die optionale Freigabe. Plattformfehler dürfen die lokale Nachrichtensendung nicht verhindern.

A22 folgt auf die grundlegende Artikel- und Medienproduktion. A23 benötigt sichere Provider, Budgetkontrolle, persistente Zustände und den geschützten Adminbereich. T206 wird zusätzlich zu T081 als Bedingung der endgültigen Gesamtabnahme geführt. Der Export kann früh geliefert werden; Korrekturübertragung und reale Publisher werden separat abgenommen. Details stehen in `../../planning/social-media-ergaenzung.yaml`.

## Ergänzung: Selbstdarstellung als Formulierungsgrundlage

Die geschützte Konfigurationsseite erhält den Bereich **Selbstdarstellung** mit Formatbeschreibung, Zielgruppe, Ton und themenspezifischen Haltungsskalen. Ein Thema kann zusätzlich einen freien Erläuterungstext erhalten. Die Zahl beschreibt die Position auf der jeweiligen Skala, nicht die Stärke des Formulierungseinflusses oder die Relevanz des Themas.

### Standardthema: Law and Order

| Wert | Bedeutung |
|---|---|
| 0 | deaktiviert |
| 1 | Gesetze sind egal |
| 50 | selbstverständlich |
| 100 | besonders wichtig |

1 ist somit eine aktive Haltung, kein nahezu abgeschaltetes Thema. 50 ist eine inhaltlich definierte Position, kein automatisch neutraler Mittelpunkt. Zwischenwerte werden abgestuft anhand der benachbarten Anker interpretiert. Jeder Textgenerator erhält Position und Skalenbeschreibungen gemeinsam; ein leerer Freitext hebt eine aktive Position nicht auf.

Weitere Standardthemen: Demokratie/Rechtsstaat, Menschenrechte/Gleichbehandlung, Klima/Umwelt, Wirtschaft/Soziales, Wissenschaft/Technik, Datenschutz/Digitalisierung und Internationales/Frieden. Für jedes Thema sind eigene verständliche Anker festzulegen. Optionale Themen umfassen Regionales, Gesundheit, Bildung, Migration/Integration, Energie, Mobilität, Kultur und Sport. Eigene Themen samt Skalenbeschreibungen sind möglich. Neue Themen sind zunächst deaktiviert (0); bestehende Nutzerwerte bleiben erhalten.

| Paket | Aufgaben | Ergebnis |
|---|---|---|
| A25 | T210–T211 | Versioniertes Schema, Formatbeschreibung, Themenpositionen und sichtbare Skalenanker in der Konfigurationsseite |
| A26 | T212–T214 | Gemeinsamer Profilkontext, Integration, Cache-Versionierung, Tests und Dokumentation |

Ein gemeinsamer `editorial_context` übergibt Formatbeschreibung und relevante aktive Themen samt Position und Skalenankern an Sprecher-, Web-, Kurz-, Überschriften-, Moderations- und Social-Textfunktionen. Werte werden nicht normalisiert. Position 0 oder explizite Deaktivierung entfernt das Thema aus dem Kontext. Es wird keine mathematisch garantierte Wirkung eines Sprachmodells behauptet.

Quellenbindung und Prüfstatus bleiben maßgeblich: Das Profil darf Wortwahl und Schwerpunkt beeinflussen, aber keine Fakten erfinden, belegte Angaben verändern oder Unsicherheit verbergen. Kommentare bleiben als solche gekennzeichnet. Profilversionen fließen in Redaktionsprotokoll und Text-Cache ein; eine Sendung nutzt einen konsistenten Snapshot.

Die Selbstdarstellung bleibt intern. Der Admin kann den tatsächlich übergebenen Kontext vorab ansehen. Lokale Fallbacks unterstützen dokumentierte Format-/Tonvorlagen; Einschränkungen bei freien Haltungen und Positionen werden offengelegt. T214 ist eine zusätzliche Freigabebedingung für T081 und für betroffene Social-Texte T206. Tests prüfen besonders die Fälle 0, 1, 50 und 100. Details stehen in `../../planning/selbstdarstellung-ergaenzung.yaml`.

## Ergänzung: Selbstsigniertes HTTPS und separater Admin-Port

Beide Betriebsarten verwenden HTTPS mit selbstsignierten Zertifikaten. Ein gemeinsamer Webdienst stellt zwei getrennte Listener bereit:

| Zweck | Vorgeschlagener Standard | Zugriff |
|---|---|---|
| Nachrichtenseite und Medien | `https://HOST` (Port `443`) | öffentlich |
| Login, Konfiguration und Admin-APIs | `https://HOST:8444` | passwortgeschützt |

Ports und Bind-Adressen sind konfigurierbar. Administrative Routen werden am öffentlichen Listener nicht registriert. Das gilt auch für die Selbstdarstellung, Exportverwaltung und Konfigurationsdateien. Ein anderer Port ersetzt die Anmeldung nicht.

**A27 (T191–T192)** umfasst Zertifikatserzeugung beim ersten Start, konfigurierbare DNS-/IP-SANs, persistente TLS-Dateien, geschützte private Schlüssel, Erneuerung, Listenertrennung und geprüfte Anleitungen für Linux, Docker CLI und Portainer. Container-Neuerstellung und Dienstneustart behalten vorhandene Zertifikate. Unbrauchbare TLS-Dateien führen zu einem Fehler statt zu HTTP-Fallback. HTTP ist standardmäßig aus.

Selbstsignierte Zertifikate verschlüsseln die Verbindung; ohne lokal eingerichtetes Vertrauen zeigt der Browser eine Zertifikatswarnung. Die Anleitung erklärt Fingerabdruckprüfung und optionales lokales Vertrauen. Admin-Sitzungen nutzen Secure-Cookies und serverseitige Port-/Origin-Prüfung; Cookies selbst sind nicht nach Ports isoliert.

T192 ist eine zusätzliche Freigabebedingung für die Betriebsabnahme T187 und die Gesamtabnahme T081. Die Anforderungen sind geplant, noch nicht implementiert.

Der öffentliche HTTPS-Standardport ist verbindlich **443**; die Nachrichtenseite ist somit ohne Portangabe erreichbar. Im Container ist eine Abbildung von Host-Port 443 auf einen internen unprivilegierten Port möglich. Beim direkten Linux-Dienst wird die erforderliche Bind-Berechtigung gezielt eingerichtet. Der Admin-Standardport bleibt 8444.

## Ergänzung: Konfigurationswizard nach erster Anmeldung

Nach der ersten erfolgreichen Admin-Anmeldung startet automatisch ein Einrichtungsassistent. Der Abschlussstatus gilt für die Installation und wird gemeinsam mit dem Entwurf dauerhaft gespeichert. Nach Abschluss führen weitere Logins zur normalen Konfiguration; dort kann der Wizard erneut geöffnet werden.

**A28 (T193–T194)** umfasst folgende Schritte:

1. Willkommen, Betriebsart und HTTPS-Adressen.
2. Formatname, Sprache, Zeitzone und Sendeplan.
3. Quellen und Rubriken.
4. Selbstdarstellung und themenspezifische Haltungspositionen.
5. Host/Stimme und Ausgabekanäle.
6. Optionale Provider und Social-Media-Ziele.
7. Zusammenfassung, vollständige Validierung und Abschluss.

Optionale Integrationen sind überspringbar. Einrichtung ohne Konten und mit Budget 0 ist möglich. Vor/Zurück und Wiederaufnahme erhalten den Entwurf; erst ein gültiger Abschluss aktiviert die Konfiguration atomar. Vorhandene Einstellungen werden übernommen statt zurückgesetzt. Zwei gleichzeitige Sitzungen dürfen Änderungen nicht stillschweigend überschreiben.

Der Wizard läuft ausschließlich nach Anmeldung am Admin-Port 8444; der öffentliche HTTPS-Port bleibt 443. Zugangsdaten bleiben über ADMIN_USER/ADMIN_PASSWORD_HASH konfiguriert. Es gibt keinen erzwungenen Passwortwechsel. T194 ist eine zusätzliche Freigabebedingung für T187 und T081. Noch nicht implementiert.

## Ergänzung: Individuelle Mitarbeiterzugänge und Freigaben

Für jeden virtuellen Mitarbeiter wird ein eigener aktivierbarer Benutzer-/Passwortzugang vorgesehen. Anmeldung und persönlicher Arbeitskorb liegen am geschützten HTTPS-Verwaltungsport 8444. Konten haben individuelle Passwort-Hashes; gemeinsame Standardpasswörter werden nicht verwendet. Der Admin aktiviert, sperrt und verwaltet diese Zugänge.

**A29 (T220–T222)** umfasst Konten, serverseitig geprüfte Rollenrechte, zugewiesene Freigabeaufgaben und ein Entscheidungsprotokoll. Je Berechtigung sind Freigabe, Ablehnung und Rückgabe zur Überarbeitung möglich. Rechte werden nach Rolle, Ressort, Show und Aufgabenzuweisung begrenzt. Ein Mitarbeiterkonto erhält dadurch keine allgemeinen Adminrechte.

Das Konto ist einer virtuellen Mitarbeiterrolle zugeordnet und wird für interaktive Entscheidungen durch einen berechtigten Bediener verwendet. Automatische KI-Rollen bleiben technisch getrennt und erhalten keine menschlichen Login-Sitzungen. Eine als menschlich erforderlich markierte Freigabe kann nicht automatisch durch die KI selbst erfolgen.

Entscheidungen beziehen sich auf eine konkrete Beitragsversion. Relevante Änderungen machen eine neue Prüfung nötig; gleichzeitige oder veraltete Entscheidungen werden kontrolliert behandelt. Protokolliert werden Konto, virtuelle Rolle, Aktion, Begründung, Zeit und Beitragsversion, niemals Zugangsdaten. Passwortwechsel oder Sperre widerrufen bestehende Sitzungen.

Der Wizard kann optional Mitarbeiterkonten und Zuständigkeiten einrichten; reiner Adminbetrieb bleibt möglich. T222 ist eine zusätzliche Freigabebedingung für T187 und T081. Details stehen in `../../planning/mitarbeiterzugang-ergaenzung.yaml`. Noch nicht implementiert.

## Präzisierung: Virtuelle Mitarbeiter sind Avatare

Ein virtueller Mitarbeiter ist eine Avatar-Identität mit Name, Darstellung, Stimme, Redaktionsrolle, Ressort und optional aktiviertem interaktivem Benutzerkonto. Redaktion und Produktion verwenden dieselbe Identität. Ein berechtigter Bediener kann über den zugeordneten Zugang Freigaben bearbeiten; automatisch arbeitende Avatar-/KI-Prozesse bleiben davon getrennt.

| Paket | Aufgaben | Ergebnis |
|---|---|---|
| A30 | T230–T232 | Gemeinsames Identitätsmodell, Avatar-Erstellungswizard, geschützter 3D-Upload und Vorschau |
| A31 | T233–T234 | Rendering, Rig-/Viseme-Zuordnung, Fallbacks, Dokumentation und Abnahme |

Der Wizard führt durch Identität, Rolle/Rechte, Darstellung, Vorschau, Stimme, optionale Kontoeinrichtung und Abschluss. Er ist aus dem Einrichtungswizard und später aus der Mitarbeiterverwaltung erreichbar. Entwürfe und Assetversionen bleiben persistent.

Als erste Uploadformate sind **GLB und glTF 2.0** geplant; GLB wird als Einzeldateiformat bevorzugt. glTF-Begleitdateien müssen explizit mit hochgeladen werden. Fremde Netzwerkreferenzen, ungültige Dateien und Ressourcenüberschreitungen werden abgelehnt. Originaldateien und Vorschau sind rechtegeschützt. Herkunft und Lizenz werden pro Avatar erfasst.

Ein beliebiges 3D-Objekt ist nicht automatisch animierbar: Der Wizard zeigt getrennt an, ob statisches Rendering, Skelettanimation und Gesicht-/Lipsync-Animation möglich sind. Dafür geeignete Rigs und Viseme/Morphziele werden überprüft und zugeordnet. Ohne diese Voraussetzungen bleibt ein statischer Avatar bzw. der bisherige Moderator-Fallback nutzbar. Zusätzliche Formate und automatische Rig-Erstellung sind keine stillschweigende Zusage.

T234 ist eine zusätzliche Freigabebedingung für T187 und T081. Die vollständigen Anforderungen stehen in `../../planning/avatar-wizard-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Studios mit Erstellungswizard und virtuellen Kameras

Studios werden als versionierte Produktionsressourcen verwaltet und Shows bzw. einzelnen Segmenten zugeordnet. Der Einrichtungswizard kann die Studioerstellung aufrufen; später ist sie in der geschützten Studioverwaltung erreichbar.

Der Studiowizard umfasst:

1. Name und Vorlage.
2. Aussehen: Hintergrund, Farben, Materialien, Logo, Tisch/Podest und Screens.
3. Avatarplätze für Einzel-/Doppelmoderation und Korrespondenten.
4. Anzahl virtueller Kameras und Einstellungen pro Kamera.
5. Beleuchtung und Vorschau aller Ansichten.
6. Show-Zuordnung, Validierung und Aktivierung.

Kameras erhalten eigene IDs und Ansichten wie Totale, Halbtotal, Nahaufnahme, Zweierbild und Screenansicht. Schnittregeln bestimmen Ansicht und Übergang je Segment bzw. Sprecherwechsel. Der Rundown speichert einen reproduzierbaren Kameraplan, den die Produktion tatsächlich umsetzt.

| Paket | Aufgaben | Ergebnis |
|---|---|---|
| A32 | T240–T242 | Studiomodell, Wizard, Assetverwaltung, Kameraeditor und Schnittregeln |
| A33 | T243–T244 | Rundown-/Renderintegration, Vorlagen, Dokumentation und visuelle Abnahme |

Für die CPU-taugliche Basis werden 2D-/2.5D-Layouts mit Bildausschnitt, Zoom und Ebenenposition genutzt. Echte 3D-Perspektiven, räumliche Lichtwirkung und Kamerabewegung benötigen einen geeigneten 3D-Renderpfad; diese Fähigkeiten werden separat ausgewiesen. Ein einzelnes Hintergrundbild wird dadurch nicht automatisch zu einem frei begehbaren 3D-Studio.

Studioassets, Kameras und Licht sind versioniert und Teil des Rendercaches. Bestehende Sendungen bleiben ihrem Studio-Snapshot zugeordnet. Quellen, Untertitel und KI-Kennzeichnungen müssen bei jedem Kamerawechsel und in Social-Formaten sichtbar bleiben. Ein Standardstudio dient als Fallback. Konten erhalten Studioverwaltungsrechte nur bei ausdrücklicher Zuweisung.

T244 ist eine zusätzliche Freigabebedingung für T187 und T081. Details stehen in `../../planning/studio-wizard-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Sendungsverwaltung und wiederkehrende Produktion

Die Showverwaltung konfiguriert Format, Quellen/Rubriken, Zieldauer, Studio, optionale Hosts/Gäste und Ausgabekanäle. Wiederkehrende Produktionspläne unterstützen tägliche und wöchentliche Termine, mehrere Uhrzeiten, Wochentage, Startdatum und Zeitzone. Vorschau der nächsten Läufe, Aktivieren/Pausieren, manuelle Testproduktion und Produktionshistorie gehören dazu. Zeitumstellung, Neustarts, verpasste Termine und Überschneidungen dürfen keine unkontrollierten Doppeljobs auslösen.

**Kein Host und kein Gast bedeutet Videoproduktion ohne Avatare.** Explizit leere Zuordnungen lösen keinen automatischen Standardhost aus. Grafiken, Bilder, Clips und passende Studio-/Screenansichten bilden das Video; Sprecherstimme und Audio werden unabhängig davon konfiguriert. Es werden keine Avatar-/Lipsync-Jobs gestartet. Nur ein Gast ohne Host ist zulässig. Zugeordnete Avatare werden nur in dafür eingeplanten Segmenten gerendert.

Alte Konfigurationen werden mit ihrer bisherigen Moderatorzuordnung migriert; bewusst leere neue Host-/Gastlisten bleiben leer. Ungültige Referenzen werden gemeldet statt durch einen anderen Host ersetzt. Produktion und Veröffentlichung sind getrennte Schritte mit bestehenden Qualitäts-/Freigaberegeln.

**A34 (T250–T252)** enthält Planung, avatarfreien Produktionspfad und Abnahme. T252 ist eine zusätzliche Bedingung für T081; der Originalgraph bleibt unverändert. Details stehen in `../../planning/sendungsverwaltung-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Zielbereiche und Zielgruppen der Selbstdarstellung

Die Selbstdarstellung enthält zusätzlich geografische und fachliche Zielbereiche sowie mehrere benannte Zielgruppen. Beispiele für Zielbereiche: eine Gemeinde, ein Bundesland, Österreich, international oder ein Themenfeld wie Wirtschaft/Technik. Zielgruppen beschreiben Interessen, Vorwissen, optional Altersgruppe, Sprache/Sprachniveau und gewünschte Erklärungstiefe. Eine Hauptzielgruppe kann festgelegt werden; ohne Angaben gilt allgemeines Publikum.

Das globale Profil dient als Standard. Jede Show kann Zielbereiche und Zielgruppen ausdrücklich überschreiben; die Konfigurationsseite zeigt das effektive Profil und seine Vererbung. Der Einrichtungswizard erhält dieselben Felder.

**T215 in A26** übergibt diese Angaben gemeinsam mit Format und Haltungsskalen an alle einschlägigen Textfunktionen. Sie beeinflussen Ansprache, Erklärungsbedarf, Wortwahl und Schwerpunkt. Sie erzeugen keine versteckten Quellenfilter; die Nachrichtenauswahl bleibt über explizite Showregeln konfiguriert. Zuschauertracking und individuelle Personenprofile sind dafür nicht erforderlich.

Profilversionen, Cache-Schlüssel und Produktionssnapshots berücksichtigen Änderungen. T215 ist zusätzlich vor abschließender Abnahme T214 und T081 nachzuweisen; der Originalgraph bleibt unverändert. Noch nicht implementiert.

## Ergänzung: Verpflichtende Archivierung aller finalen Videos

Jedes erfolgreich erzeugte finale Video wird dauerhaft auf persistentem Speicher unter **Jahr/Monat/Tag** archiviert, unabhängig davon, ob es später veröffentlicht wird. Das umfasst Showvideos, Eilmeldungen und finale Social-Media-Varianten; temporäre Rendersegmente sind ausgenommen.

Pfadschema:

```text
archive/YYYY/MM/DD/<show_id>/<production_id>/<variant_id>.mp4
```

Das Datum entspricht dem Produktionsabschluss in der Show-Zeitzone. Produktions- und Varianten-IDs verhindern Überschreiben. Ein Manifest enthält Prüfsumme, UTC-Zeit, Zeitzone und Produktionsreferenzen. Unveröffentlichte Archivvideos bleiben intern.

**A35 / T260** ersetzt die frühere Anforderung aus T030 zum automatischen Löschen alter Videos: Archivvideos werden nicht automatisch gelöscht. Nur temporäre Dateien und Caches dürfen bereinigt werden. Bei vollem Speicher oder Archivierungsfehler wird keine neue Veröffentlichung freigegeben; die letzte gültige Ausgabe bleibt verfügbar. Linux und Docker benötigen einen persistenten Archivpfad bzw. ein Archivvolume. Pages ist kein alleiniger Archivspeicher.

T260 ist zusätzliche Freigabebedingung für Betriebs- und Gesamtabnahme. Die ursprüngliche YAML bleibt als historische Vorlage unverändert; diese explizite Nutzerergänzung hat Vorrang vor widersprechenden Aufbewahrungsregeln. Details stehen in `../../planning/videoarchiv-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Bisheriges Format als initiale Newsshow

Beim ersten Start steht eine **Newsshow** mit stabiler ID `main` bereit. Sie übernimmt das bisherige Ausgabeformat und dessen Konfiguration: Quellen, Nachrichtenauswahl, Sprache, Mengen-/Dauerlimits, Moderator und Stimme, Studio, Untertitel, Ausgabekanäle und vorhandenen Zeitplan. Bei einer Neuinstallation dienen die bisherigen Projektdefaults als Basis.

**T253 in A34** stellt diese idempotente Initialisierung bzw. Legacy-Migration bereit. Vorhandene Shows werden nicht ergänzt oder überschrieben, nur um eine Defaultshow zu erzwingen. Explizit leere Host-/Gastlisten bleiben avatarfrei. Öffentliche Video-/Feed-URLs und historische Daten bleiben erhalten.

Der erste Wizard zeigt die importierte Newsshow zur Prüfung und Anpassung. Erst nach Abschluss der Ersteinrichtung wird der bestätigte automatische Produktionsplan aktiviert. Eine vorhandene Konfiguration wird vor Migration gesichert. T253 ist zusätzliche Freigabebedingung für die Showabnahme T252 und Gesamtabnahme T081. Noch nicht implementiert.

## Ergänzung: Nachrichtenblock als Sendungsbaustein

**T254 in A34** macht den Nachrichtenblock (`news_block`) zu einer versionierten, wiederverwendbaren Vorlage. Shows können mehrere Nachrichtenblöcke neben anderen Segmenten an beliebiger Stelle enthalten, etwa Regionalnachrichten, Wirtschaft und Technik. Jede Einbindung erhält eine ausdrücklich sichtbare Filterkonfiguration bzw. lokale Überschreibung.

Filter umfassen Themen/Rubriken, Regionen, Quellen, ein-/ausgeschlossene Stichwörter, Aktualität sowie Prüf-/Freigabestatus. Anzahl, Zielzeit, Sortierung und Quellengewichtung sind separat konfigurierbar. Diese Filter wählen Nachrichten aus; die Selbstdarstellung steuert weiterhin die Formulierung.

Quellenverbote und Freigabegates haben Vorrang vor jedem Blockfilter. Innerhalb einer Show werden Ereignisse standardmäßig nicht mehrfach verwendet. Bei leerem Ergebnis wird je nach Einstellung übersprungen, ein Leerhinweis gezeigt oder abgebrochen; Filter werden nie stillschweigend gelockert. Eine Vorschau zeigt Auswahl, Ausschlussgründe und geschätzte Dauer.

Der bisherige Nachrichtenabschnitt wird als erste Blockvorlage für die initiale Newsshow übernommen. Avatarfreie Produktion bleibt möglich. Filterversion und Auswahl werden pro Produktion nachvollziehbar gespeichert. T254 ist zusätzliche Freigabebedingung für T252 und T081. Noch nicht implementiert.

## Ergänzung: Studiogespräch mit Gästen

**T255 in A34** ergänzt den Sendungsbaustein `studio_conversation`: ein Newshost und eine konfigurierbare Liste von einem oder mehreren Avatar-Gästen. Eine Show kann ihn beispielsweise nach dem Nachrichtenblock einsetzen. Die Anzahl richtet sich nach verfügbaren Studioplätzen und dem geprüften Rendererlimit, nicht nach einer fest vorgegebenen Zweierbesetzung.

Konfigurierbar sind Teilnehmer und Stimmen, Studio und Plätze, Thema, Quellen, Gesprächsleitfaden/Fragen, Redezeiten, Zieldauer und Zusammenfassung. Der Host führt durch das Gespräch. Sprecherwechsel steuern Audio, Avataranimation und Kameras; Totale, Hostansicht, Gastnahaufnahme und Gruppenansicht werden im Kameraplan festgehalten.

Manuelle Dialoge und optionale KI-Dialogerzeugung werden getrennt unterstützt. Synthetische Gespräche sind gekennzeichnet; Quellenbindung und sichtbare Trennung von Meinung/Analyse bleiben maßgeblich. Fehlende Teilnehmer oder Studioplätze lösen eine konfigurierte Skip-/Abbruchregel aus, keine automatische Erfindung von Avataren. Die allgemeine avatarfreie Ausgabe bleibt für andere Segmente möglich.

Abnahme mit Host plus einem und zwei Gästen; größere Gruppen benötigen einen ausgewiesenen Kompatibilitätsnachweis. T255 ist zusätzliche Freigabebedingung für T252 und T081. Noch nicht implementiert.

## Ergänzung: Sendungsbausteine als Plugins

Sendungsbausteine werden als Plugins der Anwendung umgesetzt. Erste mitgelieferte Plugins sind **Nachrichtenblock** (`news_block`) und **Studiogespräch** (`studio_conversation`); geeignete Intro-/Outrotypen verwenden dieselbe Schnittstelle. Dies sind keine Codex-Plugins.

**A36 (T270–T272)** definiert Manifest, Konfigurationsschema, API-Version, Fähigkeiten und einen gemeinsamen Lifecycle für Validierung, Planung, Renderauftrag und Ergebnisprüfung. Die Registry liefert dem Showeditor einen Plugin-Katalog. Shows kombinieren mehrere Plugininstanzen mit unterschiedlicher Konfiguration und Reihenfolge.

Plugins verwenden zentrale Provider-, Studio-, Avatar- und Archivdienste. Veröffentlichung, Freigaben, Quellen-/KI-Kennzeichnung und Budgetprüfung bleiben beim Orchestrator. Pluginversionen werden in Produktionssnapshots und Caches gespeichert. Ein neues Plugin soll ohne Änderung des zentralen Orchestrators ergänzbar sein.

Der Vertrag T270 gehört vor die konkrete neue Bausteinimplementierung. T254/T255 spezifizieren weiterhin deren fachliche Funktionen; T271 integriert bzw. migriert sie in die Registry. Die bisherigen Aufgabenvorgänger bleiben gültig, ergänzt um diese Architekturvorgabe; daraus darf kein gegenseitiger Abhängigkeitszyklus konstruiert werden.

Installation erfolgt durch Admins als versionierter Anwendungscode. Drittanbieterplugins sind nicht automatisch sicher isoliert; beliebiger Codeupload über die Webkonfiguration ist nicht vorgesehen. Eine Entwicklungsvorlage und Installations-/Updateanleitung für Linux sowie eigene Docker-/Portainer-Images werden geliefert. T272 ist zusätzliche Freigabebedingung für T081. Noch nicht implementiert.

## Ergänzung: Immer sichtbare AI-Kennzeichnung rechts unten

Jede erzeugte visuelle Ausgabe erhält verpflichtend das Label **AI rechts unten**. In Videos bleibt es vom ersten bis zum letzten Frame sichtbar, einschließlich Intro, Abspann, Übergängen und avatarfreien Szenen. Das gilt auch für Kurzclips, Social-Media-Varianten, finale Segmente, Vorschaubilder, Thumbnails und separat ausgegebene generierte Bilder.

**A37 / T280** setzt das Label zentral nach finalem Zuschnitt und Skalierung ins Bild. Es ist kontrastreich, lesbar, mit sicherem Randabstand positioniert und nicht abschaltbar. Studios und Plugins können es nicht umgehen. Archiviert und veröffentlicht werden die gekennzeichneten finalen Artefakte. Spezifische Symbolbild-/KI-Moderatorhinweise bleiben zusätzlich bestehen.

Reine Audio-/Textausgaben erhalten passende Metadaten-/Texthinweise statt eines räumlichen Bildlabels. Die allgemeine Abschaltbarkeit neuer Funktionen aus C4 gilt ausdrücklich nicht für diese vom Nutzer geforderte Pflichtkennzeichnung. T280 ist zusätzliche Freigabebedingung für T081 und sämtliche visuellen Export-/Veröffentlichungsabnahmen. Noch nicht implementiert.

## Ergänzung: Themenkurzvideos virtueller Mitarbeiter

Virtuelle Mitarbeiter können beauftragte Kurzvideos zu einem Thema erstellen. Im geschützten Arbeitsbereich werden Thema/Leitfrage, Quellen, Zielgruppe, Sprache, Dauer und Ausgabeformat festgelegt. Selbstdarstellung und Haltungsprofil fließen in die Formulierung ein. Der Mitarbeiter verantwortet die Bearbeitung; sein Avatar kann optional als Präsentator auftreten. Explizit avatarfreie Ausgabe bleibt möglich.

**A38 (T290–T291)** umfasst Aufträge, beleggebundene Skripterstellung, Prüfung, Vorschau/Freigabe und Rendering. Das Plugin `topic_short` unterstützt sowohl eigenständige Kurzvideos als auch die Einbindung in eine Show. KI-Schritte können automatisch ablaufen, ersetzen aber keine erforderliche menschliche Freigabe.

Die Produktion verwendet bestehende Provider-, Ressourcen-, Studio- und Avatarverträge. Finale Videos werden verpflichtend unter Jahr/Monat/Tag archiviert und tragen durchgehend rechts unten AI. Social-Veröffentlichung bleibt separat aktiviert und berechtigt. T291 ist zusätzliche Freigabebedingung für T081. Details stehen in `../../planning/mitarbeiter-kurzvideos-ergaenzung.yaml`. Noch nicht implementiert.

## Präzisierung: Themenquelle für Mitarbeiter-Kurzvideos

**T292 in A38** stellt zwei Eingangswege bereit:

1. Auswahl aus den bereits vorhandenen Themengruppen/Clustern mit ihren Meldungen und Quellen.
2. Ein freier Beitrag mit Titel, Text und optionalen Bild-, Audio- oder Videodateien.

Freie Beiträge werden als manueller Eingang in dasselbe Datenmodell und denselben Redaktionsworkflow wie RSS-Meldungen übernommen. Herkunft, Zeitstempel, Quellen-/Mediennachweise und Versionen bleiben nachvollziehbar; eine RSS-URL oder unabhängige Bestätigung wird nicht erfunden. Ein Upload ist kein Freigabe- oder Vertrauensnachweis.

Kategorisierung, Gruppierung, Claim-/Quellenprüfung, Formulierung und Freigabe gelten gleichermaßen. Rohuploads bleiben geschützt; öffentliche Verwendung ist separat geregelt. Eine abgeleitete Transkription oder Medienbeschreibung zählt nicht als zusätzliche unabhängige Quelle. T292 ist vor abschließender Kurzvideoabnahme T291 und T081 nachzuweisen. Noch nicht implementiert.

## Ergänzung: Intro/Outro je Show und Kurzvideo

Die Redaktionsverwaltung erhält eine **Sequenzbibliothek**. Berechtigte Mitarbeiter erzeugen dort Standard-Intros und -Outros mit Text, Stimme, optionalen Avataren/Studios, Grafiken, Logo und Audio. Vorschau, Freigabe, Versionen und passende Ausgabevarianten gehören zur Verwaltung.

**A39 (T300–T302)** macht diese zuvor gerenderten Sequenzen je Show und Kurzvideo auswählbar. Intro und Outro können unabhängig gewählt oder deaktiviert werden. Übernommene Vorgaben und individuelle Auswahl werden im Editor sichtbar. Wiederverwendung startet keine erneute KI-Generierung. Bestehende Sequenzen der initialen Newsshow werden übernommen.

Der Rundown berücksichtigt die Sequenzdauer in der Gesamtlänge. Seitenverhältnis, Sprache und Ton müssen zur Ausgabe passen. Auswahl verweist auf eine konkrete Version; Aktualisierung erfolgt bewusst, historische Produktionen bleiben unverändert. Alle finalen Sequenzvideos sind archiviert und rechts unten mit AI gekennzeichnet. T302 ist zusätzliche Freigabebedingung für T081. Details stehen in `../../planning/intro-outro-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Sendungsblock-Plugin Uploadvideo

**A40 / T310** ergänzt das Plugin `uploaded_video`. Berechtigte Benutzer laden ein Video hoch oder wählen ein vorhandenes Uploadasset und fügen es an gewünschter Stelle einer Show ein. Vorschau, optionaler Start-/Endzuschnitt, Tonsteuerung und Einpassung in das Ausgabeformat sind konfigurierbar; die tatsächliche Dauer fließt in den Rundown ein.

Uploadprüfung, Medienrechte, Herkunft und erforderliche Freigaben bleiben verbindlich. Das geschützte Original wird unverändert aufbewahrt; abgeleitete finale Blockvideos und Showausgaben werden im Pflichtarchiv gespeichert. Die produzierte Ausgabe trägt rechts unten AI, ohne die Herkunft des Originalvideos fälschlich als KI-generiert zu beschreiben. Avatarproduktion ist für diesen Block nicht nötig.

Fehlende oder ungültige Assets werden vor Produktion erkannt. Das Plugin nutzt dieselben Schnittstellen und Gates wie andere Bausteine. T310 ist zusätzliche Freigabebedingung für T081. Details stehen in `../../planning/uploadvideo-plugin-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Konfigurationsreiter Unterstützung

**A41 (T320–T322)** ergänzt den Reiter **Unterstützung** für Auswahl, Aktivierung, sichere Zugangsdaten, Modell-/Endpointkonfiguration, Verbindungstests und Zuordnung von KI-Diensten zu Produktionsaufgaben. Der Einrichtungswizard nutzt dieselbe Verwaltung.

- Lokal: Ollama, llama.cpp, LocalAI, ComfyUI, stable-diffusion.cpp; optional Docker Model Runner. Modelle und Fähigkeiten werden getrennt von Laufzeiten geführt.
- 0-Euro-Kontingente: Gemini, Groq und Mistral als zu prüfende Kandidaten. Bedingungen und konkrete Konto-/Modellverfügbarkeit sind maßgeblich, keine Garantie kostenloser Dauerproduktion.
- Kommerziell: OpenAI, Anthropic, Google, Mistral sowie für Medien Black Forest Labs und Runway. Fähigkeiten und Adapterstatus werden ausdrücklich angezeigt.

Gespeicherte API-Keys/Tokens bleiben serverseitig geschützt und werden nicht zurück an den Browser ausgegeben. Extern gesetzte Secrets erscheinen als extern verwaltet. Kostenmodus und Budget werden explizit gewählt; kostenloser Betrieb wechselt bei Quota-Ausfall nicht automatisch in bezahlten Betrieb. Anbieter werden durch Katalogaufnahme weder installiert noch aktiviert. Unimplementierte Adapter sind entsprechend markiert.

Die aktuellen offiziellen Nachweise sind in `../../planning/unterstuetzung-ergaenzung.yaml` verlinkt. Gemini dokumentiert einen modellabhängigen Free Tier, Groq kontingentierte Limits und Mistral einen kostenlosen Modus für Evaluation/Prototypen. Konkrete Limits werden vor realer Aktivierung geprüft. T322 ist zusätzliche Freigabebedingung für T081. Noch nicht implementiert.

## Ergänzung: Kostenvorschau je Show

**A42 / T330** zeigt vor Produktion die geschätzten Kosten je Show und Produktionsschritt: Text, Bilder, Sprache, generative Clips und Avatare nach ausgewähltem Provider und Modell. Vorhandene Sequenzen, Uploadvideos und Cachetreffer werden berücksichtigt. Lokale Nutzung ist als 0 Euro externe API-Kosten ausgewiesen, Strom-/Hardwarekosten nur mit separaten hinterlegten Daten.

Die Vorschau nennt Erwartungswert, konservativen Kostenrahmen, Annahmen und Preisstand. Unbekannte oder veraltete Preise erscheinen als unbekannt; kostenlose Restkontingente werden nicht einfach vorausgesetzt. Der Kalender des wiederkehrenden Sendeplans liefert Prognosen für Restmonat und nächsten vollen Monat. Unsichere Wiederholungen und gemeinsame Kontingente bleiben sichtbar.

Budgets werden vor Start reserviert und im Lauf weiter geprüft. Eine Prognose ist keine Garantie einer exakten Anbieterrechnung. Änderungen machen die Vorschau ungültig; nach dem Lauf werden Schätzung und erfasster Verbrauch verglichen. Die Berechnung selbst löst keine kostenpflichtige Generierung aus. T330 ist zusätzliche Freigabebedingung für T081. Details stehen in `../../planning/kostenvorschau-ergaenzung.yaml`. Noch nicht implementiert.

## Ergänzung: Produktion und Veröffentlichung sind getrennte Vorgänge

**A43 (T340–T341)** trennt Aufträge, Termine, Rechte und Status für Produktion und Veröffentlichung. Ein Produktionslauf erzeugt, prüft und archiviert die Ausgabe ausschließlich intern. Er ändert weder öffentliche Website/Feeds noch Social-Media-Ziele. Erst ein eigener Veröffentlichungsauftrag schaltet konkrete Artefaktversionen für ausgewählte Kanäle frei.

Beispiel: Produktion täglich 06:30, interne Sichtung/Freigabe, Veröffentlichung 07:00. Alternativ manuelle Veröffentlichung oder ausdrücklich aktivierte Automatik nach Produktion. Ohne entsprechende Konfiguration bleibt die Ausgabe intern. Fehlt die passende Produktion oder Freigabe, wird nicht stillschweigend ein anderes Video veröffentlicht.

Veröffentlichen verwendet fertige Artefakte ohne erneutes Rendering. Version, Quellen-/Qualitätsprüfung, AI-Label und Archivintegrität bleiben verbindlich. Pro Zielkanal werden Erfolg, Fehler und Wiederholungen getrennt geführt. Rechte für Produzieren, Freigeben und Veröffentlichen sind unabhängig. Archivvorschau und Originaldateien bleiben vor Freischaltung geschützt.

Diese Ergänzung hat Vorrang vor der früheren T250-Vorgabe einer standardmäßigen Veröffentlichung nach Produktion; die ergänzende Showplanung ist entsprechend korrigiert. Neue Installationen aktivieren Veröffentlichung nur ausdrücklich. Bestehende eingerichtete Regeln werden bei Migration sichtbar übernommen. T341 ist zusätzliche Freigabebedingung für T081. Noch nicht implementiert.

## Versionszuordnung

Die vollständige Aufteilung aller 140 Aufgaben und 44 Pakete auf 0.1 bis 1.0 steht in [Versionsplan](versionen-newsoutlet.md) und `../../planning/versionen-0.1-bis-1.0.yaml`. Große Pakete sind auf mehrere Abschlussversionen verteilt; maschinenlesbare Aufgabenabhängigkeiten wurden geprüft.
