# Versionsplan 0.1 bis 1.0

Stand: 29.10.2026. **140 Aufgaben in 44 Arbeitspaketen**, vollständig auf zehn Versionen verteilt. Alles ist geplant; Versionsnummern sind keine Aussage über bereits vorhandene Implementierung oder Termine.

Die Aufteilung orientiert sich an den bestehenden Abhängigkeiten. Ein großes Paket darf über mehrere Versionen laufen; eine Aufgabe wird genau einer Abschlussversion zugeordnet. Innerhalb einer Version gilt die topologische Reihenfolge. Bereits vorhandene Funktionen bleiben erhalten, werden aber vor Übernahme überprüft.

## Release-Regeln

- Bis einschließlich 0.8 sind dies Entwicklungs-/Testmeilensteine, keine Freigabe des neuen Systems zur unbeaufsichtigten öffentlichen Produktion. Die komplette Trennung von Produktion und Veröffentlichung wird in 0.9 abgenommen. Bis dahin bleiben neu entwickelte Produktionspfade intern; vorhandener Altbetrieb ist separat zu betrachten.
- Technische Archiv-/HTTPS-Grundlagen entstehen früh; eine neue End-to-End-Produktion wird erst mit verbindlichem AI-Label und Pflichtarchiv abgenommen.
- Tests, Dokumentation und Sicherheits-/Berechtigungsprüfungen begleiten jede Version. T072/T073 werden nach ihrem ersten Abschluss weiter gepflegt.
- Explizite zusätzliche Freigabebedingungen aus dem Umsetzungsplan bleiben verbindlich, auch wenn sie nicht in historischen depends_on-Feldern stehen. Beispielsweise werden T214/T291/T252/T081 erst als öffentlich releasefähig betrachtet, wenn ihre ergänzten Prüfungen erfüllt sind.
- Lokale CPU-Fallbacks bleiben Basis. Reale Provider und anspruchsvolles 3D/Lipsync haben separate Hardware-/Qualitätsnachweise. Ungeprüfte Funktionen werden nicht als produktionsfähig ausgewiesen.
- TYPO3 und echte Mandantenisolierung sind bislang diskutierte Architekturthemen, keine zusätzlich angenommenen Aufgaben dieser 140er-Basis. Vor Implementierung dazu eine eigene Entscheidung treffen.

## Übersicht

| Version | Ziel | Aufgaben |
|---|---|---:|
| 0.1 | Fundament und Nachrichtenauswahl | 14 |
| 0.2 | Linux/Docker, gesicherter Betrieb und Archiv | 29 |
| 0.3 | Redaktionskern, Belege und Pluginvertrag | 19 |
| 0.4 | Konfiguration, Selbstdarstellung, Wizard und Rechte | 16 |
| 0.5 | Avatare und Studiogestaltung | 17 |
| 0.6 | Modulare Shows und gekennzeichnete Produktion | 11 |
| 0.7 | Weitere Medien und Ausgabekanäle | 18 |
| 0.8 | Kurzvideos, Sequenzen und Social-Veröffentlichung | 9 |
| 0.9 | Getrennte Veröffentlichung, Kosten und Betriebsabnahme | 5 |
| 1.0 | Stabilisierung, Migration und Gesamtabnahme | 2 |

## 0.1 – Fundament und Nachrichtenauswahl

Abnahme: Schema, CI, Provider-Mocks und deterministische Nachrichtenauswahl sind geprüft; keine Produktion externer Inhalte.

Beteiligte Pakete: A00, A01, A02, A03.

- **A00 – Bestand und Schnittstellen:** T001 Code- und Workflow-Inventar erstellen.
- **A01 – Schema, CI und Sicherheit:** T002 Konfigurationsschema einfuehren; T072 Testabdeckung und CI; T073 Datenschutz und Sicherheit.
- **A02 – Provider-Grundlage ohne externe Aufrufe:** T100 Provider-Interface, Registry und Mock-Provider; T101 Budget- und Quota-Waechter; T103 Ergebnis-Cache und Idempotenz; T104 Datenabfluss-Filter und Protokoll; T130 Analyse-Aufgaben und Ausgabeschemata; T135 Prompt-Injection-Schutz fuer Feed-Inhalte.
- **A03 – Shows und Nachrichtenauswahl:** T010 Mehrere Sendungsformate (Editionen) unterstuetzen; T011 Rubriken und Themenzuordnung; T012 Duplikat- und Themenclustering; T052 Quellen-Blockliste und Gewichtung.

## 0.2 – Linux/Docker, gesicherter Betrieb und Archiv

Abnahme: Linux- und Docker-Basis, HTTPS 443/8444, Login und persistentes Archiv sind technisch geprüft. Noch kein vollständiger neuer Produktionsbetrieb.

Beteiligte Pakete: A04, A05, A06, A07, A09, A18, A19, A20, A21, A27, A35.

- **A04 – Veröffentlichung und Betrieb absichern:** T051 Qualitaetspruefungen vor Veroeffentlichung; T070 Planung und Laufzeitbudget in Workflows; T071 Fehlerbehandlung, Wiederholung und Benachrichtigung.
- **A05 – Artikel und Herkunftsnachweise:** T020 Statische Artikelseiten pro Meldung; T050 Quellentransparenz und Kennzeichnung KI-generierter Inhalte; T062 Bildquellen und Lizenzen; T124 Bild- und Medienherkunft pruefen.
- **A06 – Eilmeldungen und Webnavigation:** T013 Eilmeldungs-Modus (Breaking News); T021 Startseite im Redaktionslayout; T022 Rubrikenseiten und Sendungsseiten; T032 Sitemap, Metadaten und Teilen.
- **A07 – Archiv und Suche:** T030 Archiv mit Aufbewahrungsregeln; T031 Clientseitige Volltextsuche.
- **A09 – Präsentation und Untertitel:** T060 Mehrere Moderatoren und Studio-Varianten; T061 Grafikbausteine (Einblendungen); T063 Untertitel verbessern.
- **A18 – Linux-Installation und Dienst:** T180 Betriebsvertrag für Linux und Container; T181 Repository-Installation unter Linux; T182 Start-/Stop-Skripte und Linux-Dienst.
- **A19 – Docker, CLI und Portainer:** T183 Docker-Image und Compose-Betrieb; T184 Installationsanleitung für Docker CLI; T185 Installationsanleitung für Portainer.
- **A20 – Persistenz und Betriebsabnahme:** T186 Persistenz, Updates und Betriebsdiagnose.
- **A21 – Admin-Authentifizierung der Konfiguration:** T188 Admin-Zugang über Laufzeitvariablen; T189 Konfigurationsseite und API serverseitig schützen; T190 Admin-Konfiguration in CLI-/Portainer-Dokumentation und Abnahme.
- **A27 – HTTPS und separater Admin-Port:** T191 HTTPS mit selbstsignierten Zertifikaten und getrennten Listenern; T192 HTTPS-Installation, Portainer und Zugriffstests.
- **A35 – Verpflichtendes datumsbasiertes Videoarchiv:** T260 Verpflichtendes Videoarchiv Jahr/Monat/Tag.

## 0.3 – Redaktionskern, Belege und Pluginvertrag

Abnahme: Redaktionsworkflow und beleggestütztes Routing laufen mit Fixtures; Pluginvertrag und Rundown sind definiert.

Beteiligte Pakete: A10, A11, A12, A14, A36.

- **A10 – Virtuelle Redaktion und Planung:** T110 Redaktionsmodell - Abteilungen und virtuelle Mitarbeiter; T111 Redaktionsworkflow als Zustandsautomat; T112 Rollen-Prompts und Stilhandbuch; T113 Redaktionskonferenz und Sendungsplanung; T114 Redaktionsprotokoll und Seite "Unsere Redaktion".
- **A11 – Anbieterprüfung und Beleggewinnung:** T102 Anbieter-Bewertung und Dokumentation; T120 Claim-Extraktion; T121 Mehrquellen-Abgleich; T122 Externe Fact-Check-Quellen anbinden; T123 Primaerquellen-, Zahlen- und Zitatpruefung.
- **A12 – Bewertung, Freigabe und Korrekturen:** T132 Mehr-Anbieter-Strategie und zweite Meinung; T125 Verdikt-Modell, Schwellen und Veroeffentlichungs-Gate; T126 Korrekturen und Updates; T127 Fact-Check-Anzeige in Web und Video; T128 Menschliche Freigabe bei unsicheren Meldungen; T129 Fact-Check-Testkorpus und Metriken.
- **A14 – Formate und Segmentproduktion:** T150 Show-Format-Katalog; T151 Segment-Engine und Rundown.
- **A36 – Pluginarchitektur für Sendungsbausteine:** T270 Pluginvertrag und Registry für Sendungsbausteine.

## 0.4 – Konfiguration, Selbstdarstellung, Wizard und Rechte

Abnahme: Geschützte Konfiguration, Wizard, Mitarbeiterrechte und Profilkontext funktionieren mit Mocks; lokale/Cloud-Dienste explizit konfigurierbar.

Beteiligte Pakete: A13, A25, A26, A28, A29, A41.

- **A13 – Texterstellung und Analyseformate:** T131 Nachrichtenformulierung (Sprechertext, Webtext, Kurzfassung); T133 Grounding-Pruefung gegen Halluzinationen; T134 Urheberrechts- und Originalitaetsschutz; T115 Getrennte Kommentar- und Analyseabteilung.
- **A25 – Selbstdarstellung: Datenmodell und Konfigurationsseite:** T210 Datenmodell für Selbstdarstellung und Themenhaltungen; T211 Konfigurationsoberfläche für Selbstdarstellung.
- **A26 – Selbstdarstellung: Textkontext und Abnahme:** T212 Gemeinsamer Profilkontext für Textfunktionen; T215 Zielbereiche und Zielgruppen der Selbstdarstellung.
- **A28 – Einrichtungswizard nach erster Anmeldung:** T193 Konfigurationswizard bei erster Admin-Anmeldung; T194 Wizard-Dokumentation und Abnahme.
- **A29 – Mitarbeiterzugänge und persönliche Freigabeaufgaben:** T220 Individuelle Zugänge für virtuelle Mitarbeiter; T221 Rollenrechte und zugewiesene Freigabeaufgaben; T222 Freigabeprotokoll, Dokumentation und Abnahme.
- **A41 – Unterstützung: lokale und Cloud-KI konfigurieren:** T320 Konfigurationsreiter Unterstützung und Anbieterkatalog; T321 Zugangsdaten, Verbindungsprüfung und Aufgabenzuordnung; T322 Anbieterreiter dokumentieren und abnehmen.

## 0.5 – Avatare und Studiogestaltung

Abnahme: Avatar-/Studiowizards und 3D-Upload zeigen ihre tatsächlichen Fähigkeiten; Fallbacks sind nutzbar.

Beteiligte Pakete: A15, A16, A30, A32.

- **A15 – Optionale externe Videoclips:** T140 Video-Provider-Adapter mit asynchronen Jobs.
- **A16 – Avatare, Stimmen und Korrespondenten:** T160 Avatar-Anforderungen und Technologie-Evaluierung; T161 Avatar-Provider-Adapter; T163 Natuerliche deutsche Stimmen; T164 Fiktive Host-Identitaeten; T162 Echtes Lipsync (audiogetrieben); T165 Natuerlichkeit und Studio-Integration; T166 Render-Strategie, Cache und Kosten; T167 Kennzeichnung und Ethik-Richtlinie synthetischer Moderatoren; T168 Automatische Qualitaetskontrolle von Avatar und Lipsync; T152 Korrespondenten-Segment (Schalte).
- **A30 – Avataridentität, Erstellungswizard und 3D-Upload:** T230 Gemeinsames Mitarbeiter-/Avatarmodell; T231 Avatar-Erstellungswizard und Assetverwaltung; T232 3D-Upload, Validierung und Vorschau.
- **A32 – Studiomodell, Wizard und Kameraeditor:** T240 Versioniertes Studiomodell und Produktionszuordnung; T241 Studio-Erstellungswizard und Verwaltung; T242 Kameraeditor und Schnittregeln.

## 0.6 – Modulare Shows und gekennzeichnete Produktion

Abnahme: Initiale Newsshow, gefilterte Nachrichten- und Gesprächsplugins sowie Studio-/Kameraproduktion funktionieren; alle finalen Ausgaben tragen AI und werden archiviert.

Beteiligte Pakete: A14, A31, A33, A34, A36.

- **A14 – Formate und Segmentproduktion:** T153 Roundtable- und Diskussionsformat.
- **A31 – 3D-Produktion und Avatarabnahme:** T233 3D-Rendering, Rigging-Zuordnung und Lipsync-Fallback; T234 Avatarwizard-Dokumentation und Abnahme.
- **A33 – Studioproduktion, Vorlagen und Abnahme:** T243 Studiointegration in Rundown und Renderer.
- **A34 – Wiederkehrende Sendungen und avatarfreie Produktion:** T250 Sendungsverwaltung und wiederkehrende Produktionspläne; T251 Avatarfreie Produktion bei fehlenden Hosts und Gästen; T253 Bisheriges Ausgabeformat als initiale Newsshow übernehmen; T254 Nachrichtenblock als wiederverwendbarer Sendungsbaustein mit redaktionellem Filter; T255 Studiogespräch mit Newshost und konfigurierbarer Gästezahl.
- **A36 – Pluginarchitektur für Sendungsbausteine:** T271 Nachrichtenblock und Studiogespräch als mitgelieferte Plugins; T272 Plugin-Entwicklungsvorlage, Dokumentation und Abnahme.

## 0.7 – Weitere Medien und Ausgabekanäle

Abnahme: Uploadvideo, zusätzliche Feeds und Medienexporte sind geprüft; optionale generative Clips erfüllen Budget-/Kennzeichnungsregeln.

Beteiligte Pakete: A08, A15, A22, A26, A33, A37, A39, A40.

- **A08 – Feeds und weitere Ausgabekanäle:** T040 Feeds pro Show und Rubrik; T041 Audio-Podcast-Feed; T042 Telegram erweitern (optional, abschaltbar); T043 Woechentlicher Newsletter als statische Datei.
- **A15 – Optionale externe Videoclips:** T141 Szenenplanung und Shot-Liste; T142 Qualitaets- und Sicherheitspruefung generierter Clips; T143 Schnitt und Komposition externer Clips; T144 Kosten- und Zeitsteuerung fuer Videojobs; T145 Kennzeichnung von KI-Videomaterial.
- **A22 – Social-Media-Profile und Export:** T200 Plattformprofile und Ausgabe-Konfiguration; T201 Plattformgerechte Videos und Bilder; T202 Texte, Links und Exportpakete.
- **A26 – Selbstdarstellung: Textkontext und Abnahme:** T213 Integration, Quellenbindung und Nachvollziehbarkeit; T214 Dokumentation und Abnahme der Selbstdarstellung.
- **A33 – Studioproduktion, Vorlagen und Abnahme:** T244 Studiovorlagen, Dokumentation und Abnahme.
- **A37 – Verpflichtendes AI-Label in allen visuellen Ausgaben:** T280 AI-Kennzeichnung in jeder visuellen Ausgabe rechts unten.
- **A39 – Redaktionelle Sequenzbibliothek und Intro-/Outroauswahl:** T300 Sequenzbibliothek für Standard-Intros und -Outros.
- **A40 – Sendungsblock-Plugin Uploadvideo:** T310 Sendungsblock-Plugin Uploadvideo.

## 0.8 – Kurzvideos, Sequenzen und Social-Veröffentlichung

Abnahme: Mitarbeiter-Kurzvideos aus Clustern/Uploads, wiederverwendbare Intros/Outros und verfügbare Social-Publisher sind abgenommen.

Beteiligte Pakete: A23, A24, A38, A39.

- **A23 – Optionale Social-Media-Publisher:** T203 Optionale Publisher und Anbieterprüfung; T204 Veröffentlichungswarteschlange und Freigabe.
- **A24 – Social-Media-Korrekturen und Abnahme:** T205 Korrekturen und Kennzeichnung auf Social Media; T206 Social-Media-Dokumentation und Abnahme.
- **A38 – Themenkurzvideos virtueller Mitarbeiter:** T290 Themenbezogene Kurzvideoaufträge für virtuelle Mitarbeiter; T291 Kurzvideo-Plugin, Ausgabe und Abnahme; T292 Themenauswahl aus Gruppen und freie Beiträge als RSS-äquivalenter Eingang.
- **A39 – Redaktionelle Sequenzbibliothek und Intro-/Outroauswahl:** T301 Intro-/Outroauswahl je Show und Kurzvideo; T302 Sequenzverwaltung und Wiederverwendung abnehmen.

## 0.9 – Getrennte Veröffentlichung, Kosten und Betriebsabnahme

Abnahme: Produktion und Veröffentlichung strikt getrennt; Zeitpläne, Kostenvorschau, Rechte und Wiederaufnahme sind im Gesamtsystem geprüft.

Beteiligte Pakete: A20, A34, A42, A43.

- **A20 – Persistenz und Betriebsabnahme:** T187 Abnahme beider Installationswege.
- **A34 – Wiederkehrende Sendungen und avatarfreie Produktion:** T252 Planung, Produktionshistorie und Abnahme.
- **A42 – Kostenvorschau je Show und Monatsprognose:** T330 Kostenvorschau und Monatsprognose je Show.
- **A43 – Produktion und Veröffentlichung konsequent trennen:** T340 Getrennte Produktions- und Veröffentlichungsaufträge; T341 Getrennte Verwaltung, Migration und Abnahme.

## 1.0 – Stabilisierung, Migration und Gesamtabnahme

Abnahme: Migration und vollständiger Mock-/Fallback-Abnahmelauf bestanden; reale Integrationen haben einen dokumentierten individuellen Prüfstatus.

Beteiligte Pakete: A17.

- **A17 – Migration und Gesamtabnahme:** T080 Dokumentation aktualisieren; T081 Abnahmelauf Ende-zu-Ende.

## Paketübersicht

| Paket | Inhalt | Abschlussversionen der Aufgaben |
|---|---|---|
| A00 | Bestand und Schnittstellen | 0.1 |
| A01 | Schema, CI und Sicherheit | 0.1 |
| A02 | Provider-Grundlage ohne externe Aufrufe | 0.1 |
| A03 | Shows und Nachrichtenauswahl | 0.1 |
| A04 | Veröffentlichung und Betrieb absichern | 0.2 |
| A05 | Artikel und Herkunftsnachweise | 0.2 |
| A06 | Eilmeldungen und Webnavigation | 0.2 |
| A07 | Archiv und Suche | 0.2 |
| A08 | Feeds und weitere Ausgabekanäle | 0.7 |
| A09 | Präsentation und Untertitel | 0.2 |
| A10 | Virtuelle Redaktion und Planung | 0.3 |
| A11 | Anbieterprüfung und Beleggewinnung | 0.3 |
| A12 | Bewertung, Freigabe und Korrekturen | 0.3 |
| A13 | Texterstellung und Analyseformate | 0.4 |
| A14 | Formate und Segmentproduktion | 0.3, 0.6 |
| A15 | Optionale externe Videoclips | 0.5, 0.7 |
| A16 | Avatare, Stimmen und Korrespondenten | 0.5 |
| A17 | Migration und Gesamtabnahme | 1.0 |
| A18 | Linux-Installation und Dienst | 0.2 |
| A19 | Docker, CLI und Portainer | 0.2 |
| A20 | Persistenz und Betriebsabnahme | 0.2, 0.9 |
| A21 | Admin-Authentifizierung der Konfiguration | 0.2 |
| A22 | Social-Media-Profile und Export | 0.7 |
| A23 | Optionale Social-Media-Publisher | 0.8 |
| A24 | Social-Media-Korrekturen und Abnahme | 0.8 |
| A25 | Selbstdarstellung: Datenmodell und Konfigurationsseite | 0.4 |
| A26 | Selbstdarstellung: Textkontext und Abnahme | 0.4, 0.7 |
| A27 | HTTPS und separater Admin-Port | 0.2 |
| A28 | Einrichtungswizard nach erster Anmeldung | 0.4 |
| A29 | Mitarbeiterzugänge und persönliche Freigabeaufgaben | 0.4 |
| A30 | Avataridentität, Erstellungswizard und 3D-Upload | 0.5 |
| A31 | 3D-Produktion und Avatarabnahme | 0.6 |
| A32 | Studiomodell, Wizard und Kameraeditor | 0.5 |
| A33 | Studioproduktion, Vorlagen und Abnahme | 0.6, 0.7 |
| A34 | Wiederkehrende Sendungen und avatarfreie Produktion | 0.6, 0.9 |
| A35 | Verpflichtendes datumsbasiertes Videoarchiv | 0.2 |
| A36 | Pluginarchitektur für Sendungsbausteine | 0.3, 0.6 |
| A37 | Verpflichtendes AI-Label in allen visuellen Ausgaben | 0.7 |
| A38 | Themenkurzvideos virtueller Mitarbeiter | 0.8 |
| A39 | Redaktionelle Sequenzbibliothek und Intro-/Outroauswahl | 0.7, 0.8 |
| A40 | Sendungsblock-Plugin Uploadvideo | 0.7 |
| A41 | Unterstützung: lokale und Cloud-KI konfigurieren | 0.4 |
| A42 | Kostenvorschau je Show und Monatsprognose | 0.9 |
| A43 | Produktion und Veröffentlichung konsequent trennen | 0.9 |

Maschinenlesbare vollständige Zuordnung: `../../planning/versionen-0.1-bis-1.0.yaml`. Die Aufgabenanzahl bleibt unverändert; es wurden keine Funktionen gestrichen und keine Aufgaben als umgesetzt markiert.
