# Projektplan PersonalNewsHost – überarbeiteter Umfang

Stand: 29.10.2026 · ausschließlich `Full-featured-Newsoutlet` · **140 Aufgaben in 44 Arbeitspaketen**. IDs bleiben zur Nachverfolgung erhalten; gleicher Aufgabenumfang in Zahlen bedeutet nicht gleicher Aufwand. Die frühere Original-YAML bleibt historische Quelle; bei Widersprüchen gilt `planning/umfang-vereinfacht.yaml`.

## Verbindliche Vereinfachung

**Kein CMS:** WordPress, TYPO3, andere CMS, CMS-Adapter, CMS-Container, CMS-Auswahl und CMS-spezifische externe Datenbankanbindung entfallen. Eine zusätzliche Mandantenplattform wird nicht daraus abgeleitet. Die eigene Anwendung nutzt lokale Persistenz nach technischem Bedarf.

**Genau zwei Bedienzugänge:**

| Zugang | Zuständigkeit |
|---|---|
| Konfiguration | Technischer Betrieb, Provider/Modelle, Tokens, Budgets und Verwaltung der zwei Zugänge |
| Redaktion | Ressorts, virtuelle Mitarbeiter, Inhalte, Medien, Avatare, Studios, Shows/Plugins, Produktionsaufträge und Freigaben |

Getrennte Anmeldedaten, Sitzungen und serverseitige Zugriffskontrolle. Keine individuellen Mitarbeiterkonten, Avatarpasswörter, persönlichen Benutzer-Arbeitskörbe oder zusätzliche Benutzer-/Gruppenverwaltung. Beide Bereiche nutzen den vorhandenen geschützten HTTPS-Verwaltungsport. Standard admin/admin gilt nur für Konfiguration; der gemeinsame Redaktionszugang wird im Setup eingerichtet.

## Redaktionelle Struktur und Abläufe bleiben erhalten

**Abteilung/Ressort → virtueller Mitarbeiter → Beiträge/Produktionsaufgaben.** Mitarbeiterverwaltung direkt im Ressort: anlegen, bearbeiten, zuordnen, deaktivieren; Rolle, Avatar, Stimme, Biografie und Zuständigkeiten pflegen. Einzelbeiträge und Kurzvideos werden dort **im Namen des virtuellen Mitarbeiters** beauftragt. Keine zusätzliche Loginidentität.

Eingang ist die vorhandene Themengruppierung oder ein freier Text-/Medienbeitrag, der wie ein RSS-Eintrag verarbeitet wird. Quellenprüfung, Recherche, Textbildung, Überarbeitung, Freigabe, Fristen und Korrekturen bleiben bestehen. Gemeinsamer Arbeitskorb mit Ressort-/Mitarbeiter-/Showfiltern. Automatische KI-Stufen und menschliche Freigabe bleiben getrennt. Ein gemeinsamer Zugang erlaubt keinen sicheren Nachweis einer einzelnen realen Person; das Audit unterscheidet gemeinsamen Bedienzugang und virtuelle Bearbeiterrolle.

## Shows und Produktion bleiben modular

Showplugins: Nachrichtenblock mit redaktionellen Filtern, Studiogespräch mit Host und variabler Gästezahl, Uploadvideo, Themenkurzvideo sowie Intro-/Outrobausteine. Die Redaktion erzeugt wiederverwendbare Standardsequenzen und wählt sie je Show/Kurzvideo aus. Pluginvertrag und Erweiterbarkeit bleiben erhalten.

Mehrere regelmäßig wiederkehrende Shows mit Uhrzeit, Wochentagen und Zeitzone; initiale Newsshow aus bisherigem Ausgabeformat. Kein Host und kein Gast bedeutet avatarfreies Video, unabhängig von einer optionalen Sprecherstimme. Studio- und Avatarwizards bleiben erhalten; Avatarerstellung liegt in der Mitarbeiterverwaltung des Ressorts.

**Produktion und Veröffentlichung bleiben getrennt.** Versionierte Konfiguration, interne Produktionsauftragsliste, exklusive Übernahme/Wiederaufnahme, Archiv und eigene Veröffentlichungsfreigabe sind interne Anwendungsfunktionen ohne CMS-Adapter.

## Weitere verbindliche Anforderungen

- Linux aus Repository oder Docker/Compose/Portainer; Start/Stop/Status, persistente Daten, Updates, Backup.
- Nachrichtenseite HTTPS 443, geschützte Verwaltung auf separatem konfigurierbarem Port (Standard 8444), persistente selbstsignierte Zertifikate.
- Einrichtungswizard, Unterstützung-Reiter, lokale/freie Fallbacks, explizite kostenpflichtige Aktivierung und Budgetkontrolle, Kostenvorschau je Show.
- Selbstdarstellung mit Format, Zielbereichen/-gruppen und Haltungsskalen; 0 deaktiviert. Law and Order: 1 Gesetze sind egal, 50 selbstverständlich, 100 besonders wichtig. Quellenbindung bleibt verbindlich.
- Social-Media-Exporte und optional aktivierte Publisher.
- Alle final erzeugten Videos dauerhaft unter Jahr/Monat/Tag archivieren; keine automatische Archivlöschung. Jede visuelle Ausgabe durchgehend rechts unten mit AI kennzeichnen.
- Technische Secrets bleiben getrennt von redaktionellen Daten. Snapshots, Audit, Qualitäts-/Freigabegates bleiben verbindlich.

## Versionen und Umsetzung

Die Planung 0.1–1.0 bleibt bestehen. CMS und Mitarbeiterkonten sind in keiner Version mehr Voraussetzung. Der tatsächliche 0.1-Test-/Commit-/Pushstatus steht in `planning/fortschritt.yaml`; ein VERSION-Dateiinhalt allein bestätigt keine Release-Abnahme.

[Versionszuordnung](versionen-newsoutlet.md). Maschinenlesbare Details: `planning/arbeitspakete.yaml`, `planning/versionen-0.1-bis-1.0.yaml` und referenzierte Aufgabenquellen. T220–T222 wurden ersetzt, nicht zusätzlich parallel beibehalten. Übrige fachliche Anforderungen gelten weiterhin, soweit sie nicht den gestrichenen Konten-/CMSumfang voraussetzen.

## Arbeitspakete

### A00 – Bestand und Schnittstellen

Skripte, Konfiguration, Workflows und Tests inventarisieren; vorhandene Implementierungen den 75 Aufgaben zuordnen; Datenmodell und Migrationsgrenzen festhalten.

- **T001:** Code- und Workflow-Inventar erstellen

### A01 – Schema, CI und Sicherheit

Schema und Validator entwickeln; alte Konfiguration als Fixture sichern; Validierung, Tests, Linkprüfung und Geheimnisscan in CI integrieren.

- **T002:** Konfigurationsschema einfuehren
- **T072:** Testabdeckung und CI
- **T073:** Datenschutz und Sicherheit

### A02 – Provider-Grundlage ohne externe Aufrufe

Bestehende Registry erweitern; typisierte Verträge und deterministische Mocks; Budgetreservierung und dauerhafte Verbrauchsbuchung; Cache, Allowlist und strikte Antwortvalidierung.

- **T100:** Provider-Interface, Registry und Mock-Provider
- **T101:** Budget- und Quota-Waechter
- **T103:** Ergebnis-Cache und Idempotenz
- **T104:** Datenabfluss-Filter und Protokoll
- **T130:** Analyse-Aufgaben und Ausgabeschemata
- **T135:** Prompt-Injection-Schutz fuer Feed-Inhalte

### A03 – Shows und Nachrichtenauswahl

Alte Konfiguration auf Standardshow abbilden; Ausgaben nach Show trennen; Kategorien, Quellenregeln und deterministisches Clustering ergänzen.

- **T010:** Mehrere Sendungsformate (Editionen) unterstuetzen
- **T011:** Rubriken und Themenzuordnung
- **T012:** Duplikat- und Themenclustering
- **T052:** Quellen-Blockliste und Gewichtung

### A04 – Veröffentlichung und Betrieb absichern

Vorprüfung und temporäres Ausgabeziel; erst vollständig geprüfte Artefakte veröffentlichen; Feed-Fallbacks, Zeitlimits und Show-Concurrency ergänzen.

- **T051:** Qualitaetspruefungen vor Veroeffentlichung
- **T070:** Planung und Laufzeitbudget in Workflows
- **T071:** Fehlerbehandlung, Wiederholung und Benachrichtigung

### A05 – Artikel und Herkunftsnachweise

Stabile Artikel-IDs und URLs; sichere HTML-Ausgabe; Quellen, Abrufzeit, Bildnachweise und KI-Kennzeichnung im gemeinsamen Datenmodell.

- **T020:** Statische Artikelseiten pro Meldung
- **T050:** Quellentransparenz und Kennzeichnung KI-generierter Inhalte
- **T062:** Bildquellen und Lizenzen
- **T124:** Bild- und Medienherkunft pruefen

### A06 – Eilmeldungen und Webnavigation

Eilmeldungserkennung zuerst ohne Renderkosten; Kurzclip und deduplizierte Veröffentlichung; Startseite, Kategorien, Shows und Metadaten generieren.

- **T013:** Eilmeldungs-Modus (Breaking News)
- **T021:** Startseite im Redaktionslayout
- **T022:** Rubrikenseiten und Sendungsseiten
- **T032:** Sitemap, Metadaten und Teilen

### A07 – Archiv und Suche

Sendungs- und Artikelindizes versionieren; verpflichtendes Videoarchiv nach T260 statt automatischer Archivvideo-Löschung; Suchindex mit Größenlimit und Archivseiten erstellen.

- **T030:** Archiv mit Aufbewahrungsregeln
- **T031:** Clientseitige Volltextsuche

### A08 – Feeds und weitere Ausgabekanäle

Show-/Rubrikenfeeds und Artikel-Feeds; Audio plus Kapitel; Telegram-Zuordnung; wöchentliche HTML-/Textausgabe ohne Standardversand.

- **T040:** Feeds pro Show und Rubrik
- **T041:** Audio-Podcast-Feed
- **T042:** Telegram erweitern (optional, abschaltbar)
- **T043:** Woechentlicher Newsletter als statische Datei

### A09 – Präsentation und Untertitel

Host-/Studio-Zuordnung von Avatar-Technik trennen; Grafiktemplates vereinheitlichen; SRT-Zeiten messen und WebVTT ergänzen.

- **T060:** Mehrere Moderatoren und Studio-Varianten
- **T061:** Grafikbausteine (Einblendungen)
- **T063:** Untertitel verbessern

### A10 – Virtuelle Redaktion und Planung

Rollenmodell und Rechte; persistenter Zustandsautomat mit begrenzten Korrekturschleifen; versionierte Prompts; Sendeplan und öffentliches Redaktionsprotokoll.

- **T110:** Redaktionsmodell - Abteilungen und virtuelle Mitarbeiter
- **T111:** Redaktionsworkflow als Zustandsautomat
- **T112:** Rollen-Prompts und Stilhandbuch
- **T113:** Redaktionskonferenz und Sendungsplanung
- **T114:** Redaktionsprotokoll und Seite "Unsere Redaktion"

### A11 – Anbieterprüfung und Beleggewinnung

Anbieterrecherche und Benchmark zunächst mit Mocks vorbereiten; Claim-Schema, unabhängige Quellen, Fact-Check-Hinweise und Primärquellenvergleich implementieren.

- **T102:** Anbieter-Bewertung und Dokumentation
- **T120:** Claim-Extraktion
- **T121:** Mehrquellen-Abgleich
- **T122:** Externe Fact-Check-Quellen anbinden
- **T123:** Primaerquellen-, Zahlen- und Zitatpruefung

### A12 – Bewertung, Freigabe und Korrekturen

Zweitmeinung als separaten Ergebnisdienst; regelbasiertes Routing; versionierte Korrekturen; Prüfstatusanzeige und menschliche Freigabe mit Frist; Testkorpus aufbauen.

- **T132:** Mehr-Anbieter-Strategie und zweite Meinung
- **T125:** Verdikt-Modell, Schwellen und Veroeffentlichungs-Gate
- **T126:** Korrekturen und Updates
- **T127:** Fact-Check-Anzeige in Web und Video
- **T128:** Menschliche Freigabe bei unsicheren Meldungen
- **T129:** Fact-Check-Testkorpus und Metriken

### A13 – Texterstellung und Analyseformate

Sprecher-, Web- und Kurztexte; Satz-zu-Quelle-Zuordnung; Zahlen-/Namensprüfung; Übernahmegrenzen; separate Analyse- und Kommentarstrecke.

- **T131:** Nachrichtenformulierung (Sprechertext, Webtext, Kurzfassung)
- **T133:** Grounding-Pruefung gegen Halluzinationen
- **T134:** Urheberrechts- und Originalitaetsschutz
- **T115:** Getrennte Kommentar- und Analyseabteilung

### A14 – Formate und Segmentproduktion

Drei einfache Formate zuerst; Sendeplan in zeitlichen Rundown überführen; Segmente einzeln rendern und zusammensetzen; danach Mehrstimmendialog.

- **T150:** Show-Format-Katalog
- **T151:** Segment-Engine und Rundown
- **T153:** Roundtable- und Diskussionsformat

### A15 – Optionale externe Videoclips

Job-Zustandsmodell mit Submit/Poll/Download und Wiederaufnahme; Shotliste; technische Prüfung und Sichtung; Schnitt, Sekundenlimit und Kennzeichnung.

- **T140:** Video-Provider-Adapter mit asynchronen Jobs
- **T141:** Szenenplanung und Shot-Liste
- **T142:** Qualitaets- und Sicherheitspruefung generierter Clips
- **T143:** Schnitt und Komposition externer Clips
- **T144:** Kosten- und Zeitsteuerung fuer Videojobs
- **T145:** Kennzeichnung von KI-Videomaterial

### A16 – Avatare, Stimmen und Korrespondenten

Technikvergleich vor Anbieterwahl; fiktive Identitäten und Standardstimmen; Mockadapter; audiogetriebenes Rendering; Synchronitätsmessung; Studiointegration und Korrespondentensegment.

- **T160:** Avatar-Anforderungen und Technologie-Evaluierung
- **T161:** Avatar-Provider-Adapter
- **T163:** Natuerliche deutsche Stimmen
- **T164:** Fiktive Host-Identitaeten
- **T162:** Echtes Lipsync (audiogetrieben)
- **T165:** Natuerlichkeit und Studio-Integration
- **T166:** Render-Strategie, Cache und Kosten
- **T167:** Kennzeichnung und Ethik-Richtlinie synthetischer Moderatoren
- **T168:** Automatische Qualitaetskontrolle von Avatar und Lipsync
- **T152:** Korrespondenten-Segment (Schalte)

### A17 – Migration und Gesamtabnahme

Begleitende Dokumentation konsolidieren; Fork-Migration; Ende-zu-Ende-Läufe mit zwei Shows, Mocks und erzwungenen Fehlern; optional reale Anbieter gesondert abnehmen.

- **T080:** Dokumentation aktualisieren
- **T081:** Abnahmelauf Ende-zu-Ende

### A18 – Linux-Installation und Dienst

Betriebsvertrag für Linux und Container; Repository-Installation unter Linux; Start-/Stop-Skripte und Linux-Dienst

- **T180:** Betriebsvertrag für Linux und Container
- **T181:** Repository-Installation unter Linux
- **T182:** Start-/Stop-Skripte und Linux-Dienst

### A19 – Docker, CLI und Portainer

Docker-Image und Compose-Betrieb; Installationsanleitung für Docker CLI; Installationsanleitung für Portainer

- **T183:** Docker-Image und Compose-Betrieb
- **T184:** Installationsanleitung für Docker CLI
- **T185:** Installationsanleitung für Portainer

### A20 – Persistenz und Betriebsabnahme

Persistenz, Updates und Betriebsdiagnose; Abnahme beider Installationswege

- **T186:** Persistenz, Updates und Betriebsdiagnose
- **T187:** Abnahme beider Installationswege

### A21 – Admin-Authentifizierung der Konfiguration

Admin-Zugang per ADMIN_USER/ADMIN_PASSWORD_HASH; serverseitiger Schutz der Konfiguration; CLI-/Portainer-Anleitung und Zugriffstests.

- **T188:** Admin-Zugang über Laufzeitvariablen
- **T189:** Konfigurationsseite und API serverseitig schützen
- **T190:** Admin-Konfiguration in CLI-/Portainer-Dokumentation und Abnahme

### A22 – Social-Media-Profile und Export

Plattformprofile und Ausgabe-Konfiguration; Plattformgerechte Videos und Bilder; Texte, Links und Exportpakete

- **T200:** Plattformprofile und Ausgabe-Konfiguration
- **T201:** Plattformgerechte Videos und Bilder
- **T202:** Texte, Links und Exportpakete

### A23 – Optionale Social-Media-Publisher

Optionale Publisher und Anbieterprüfung; Veröffentlichungswarteschlange und Freigabe

- **T203:** Optionale Publisher und Anbieterprüfung
- **T204:** Veröffentlichungswarteschlange und Freigabe

### A24 – Social-Media-Korrekturen und Abnahme

Korrekturen und Kennzeichnung auf Social Media; Social-Media-Dokumentation und Abnahme

- **T205:** Korrekturen und Kennzeichnung auf Social Media
- **T206:** Social-Media-Dokumentation und Abnahme

### A25 – Selbstdarstellung: Datenmodell und Konfigurationsseite

Versioniertes Schema und geschützte Konfigurationsseite mit Formatbeschreibung, themenspezifischen Haltungspositionen 0–100 und sichtbaren Skalenankern; Law and Order als Standardthema.

- **T210:** Datenmodell für Selbstdarstellung und Themenhaltungen
- **T211:** Konfigurationsoberfläche für Selbstdarstellung

### A26 – Selbstdarstellung: Textkontext und Abnahme

Gemeinsamer Profilkontext für Textfunktionen; Integration, Quellenbindung und Nachvollziehbarkeit; Dokumentation und Abnahme der Selbstdarstellung; Zielbereiche und Zielgruppen mit Showvererbung und gemeinsamem Textkontext.

- **T212:** Gemeinsamer Profilkontext für Textfunktionen
- **T213:** Integration, Quellenbindung und Nachvollziehbarkeit
- **T214:** Dokumentation und Abnahme der Selbstdarstellung
- **T215:** Zielbereiche und Zielgruppen der Selbstdarstellung

### A27 – HTTPS und separater Admin-Port

Selbstsignierte, persistente TLS-Zertifikate; getrennte öffentliche und administrative HTTPS-Listener; Dokumentation und Abnahme für Linux, CLI und Portainer.

- **T191:** HTTPS mit selbstsignierten Zertifikaten und getrennten Listenern
- **T192:** HTTPS-Installation, Portainer und Zugriffstests

### A28 – Einrichtungswizard nach erster Anmeldung

Geschützter Einrichtungsassistent mit persistentem Entwurf, optionalen Schritten, validiertem atomarem Abschluss und erneutem Öffnen.

- **T193:** Konfigurationswizard bei erster Admin-Anmeldung
- **T194:** Wizard-Dokumentation und Abnahme

### A29 – Gemeinsamer Redaktionszugang, Ressorts und Freigaben

Zwei getrennte Bedienzugänge; Ressort-Mitarbeiterverwaltung; gemeinsame Aufgaben und versionierte Freigaben.

- **T220:** Gemeinsamer Redaktionszugang getrennt von Konfiguration
- **T221:** Gemeinsamer Redaktionsarbeitsbereich und ressortbezogene Mitarbeiterverwaltung
- **T222:** Gemeinsames Freigabeprotokoll und Abnahme

### A30 – Avataridentität, Erstellungswizard und 3D-Upload

Mitarbeiter-/Avataridentität und Erstellungswizard direkt im Ressort, ohne Kontoschritte; 3D-Upload und Vorschau.

- **T230:** Gemeinsames Mitarbeiter-/Avatarmodell
- **T231:** Avatar-Erstellungswizard und Assetverwaltung
- **T232:** 3D-Upload, Validierung und Vorschau

### A31 – 3D-Produktion und Avatarabnahme

3D-Rendering, Rigging-Zuordnung und Lipsync-Fallback; Avatarwizard-Dokumentation und Abnahme

- **T233:** 3D-Rendering, Rigging-Zuordnung und Lipsync-Fallback
- **T234:** Avatarwizard-Dokumentation und Abnahme

### A32 – Studiomodell, Wizard und Kameraeditor

Versioniertes Studiomodell und Produktionszuordnung; Studio-Erstellungswizard und Verwaltung; Kameraeditor und Schnittregeln

- **T240:** Versioniertes Studiomodell und Produktionszuordnung
- **T241:** Studio-Erstellungswizard und Verwaltung
- **T242:** Kameraeditor und Schnittregeln

### A33 – Studioproduktion, Vorlagen und Abnahme

Studiointegration in Rundown und Renderer; Studiovorlagen, Dokumentation und Abnahme

- **T243:** Studiointegration in Rundown und Renderer
- **T244:** Studiovorlagen, Dokumentation und Abnahme

### A34 – Wiederkehrende Sendungen und avatarfreie Produktion

Showverwaltung mit Wiederholungsplänen, optionalen Hosts/Gästen, avatarfreiem Renderpfad und Produktionshistorie.; bisheriges Ausgabeformat als initiale Newsshow migrieren und im ersten Wizard vorauswählen.; wiederverwendbare Nachrichtenblöcke mit redaktionellen Filtern und Auswahlvorschau.; Studiogespräch mit Newshost, variabler Gästezahl, Gesprächsleitfaden und Kameraplan.

- **T250:** Sendungsverwaltung und wiederkehrende Produktionspläne
- **T251:** Avatarfreie Produktion bei fehlenden Hosts und Gästen
- **T252:** Planung, Produktionshistorie und Abnahme
- **T253:** Bisheriges Ausgabeformat als initiale Newsshow übernehmen
- **T254:** Nachrichtenblock als wiederverwendbarer Sendungsbaustein mit redaktionellem Filter
- **T255:** Studiogespräch mit Newshost und konfigurierbarer Gästezahl

### A35 – Verpflichtendes datumsbasiertes Videoarchiv

Alle final erzeugten Videos dauerhaft unter Jahr/Monat/Tag sichern, vor Veröffentlichung Integrität prüfen und persistente Archivvolumes bereitstellen.

- **T260:** Verpflichtendes Videoarchiv Jahr/Monat/Tag

### A36 – Pluginarchitektur für Sendungsbausteine

Versionierter Pluginvertrag, Registry, Plugin-Katalog im Showeditor und mitgelieferte Nachrichten-/Gesprächsplugins samt Entwicklungsvorlage.

- **T270:** Pluginvertrag und Registry für Sendungsbausteine
- **T271:** Nachrichtenblock und Studiogespräch als mitgelieferte Plugins
- **T272:** Plugin-Entwicklungsvorlage, Dokumentation und Abnahme

### A37 – Verpflichtendes AI-Label in allen visuellen Ausgaben

Nicht abschaltbare zentrale Kennzeichnung rechts unten nach finalem Zuschnitt; Prüfung vor Archivierung und Veröffentlichung.

- **T280:** AI-Kennzeichnung in jeder visuellen Ausgabe rechts unten

### A38 – Themenkurzvideos virtueller Mitarbeiter

Einzelbeiträge/Kurzvideos im Namen virtueller Mitarbeiter über den gemeinsamen Redaktionsbereich; Themencluster oder freie Text-/Medieneingänge.

- **T290:** Themenbezogene Kurzvideoaufträge für virtuelle Mitarbeiter
- **T291:** Kurzvideo-Plugin, Ausgabe und Abnahme
- **T292:** Themenauswahl aus Gruppen und freie Beiträge als RSS-äquivalenter Eingang

### A39 – Redaktionelle Sequenzbibliothek und Intro-/Outroauswahl

Standardsequenzen in Redaktionsverwaltung erzeugen; versioniert je Show und Kurzvideo als Intro/Outro auswählen und wiederverwenden.

- **T300:** Sequenzbibliothek für Standard-Intros und -Outros
- **T301:** Intro-/Outroauswahl je Show und Kurzvideo
- **T302:** Sequenzverwaltung und Wiederverwendung abnehmen

### A40 – Sendungsblock-Plugin Uploadvideo

Geschützter Videoupload, Vorschau, Zuschnitt und Einbindung über das Plugin uploaded_video mit gemeinsamen Prüfungen und Archivierung.

- **T310:** Sendungsblock-Plugin Uploadvideo

### A41 – Unterstützung: lokale und Cloud-KI konfigurieren

Providerkatalog, Aktivierung, sichere Tokens, Verbindungstests, Aufgabenrouting und Kostenmodi im Reiter Unterstützung.

- **T320:** Konfigurationsreiter Unterstützung und Anbieterkatalog
- **T321:** Zugangsdaten, Verbindungsprüfung und Aufgabenzuordnung
- **T322:** Anbieterreiter dokumentieren und abnehmen

### A42 – Kostenvorschau je Show und Monatsprognose

Vorabkosten nach Plugin/Provider schätzen; Cache und Sequenzen berücksichtigen; Monatsplan hochrechnen und mit Budgets prüfen.

- **T330:** Kostenvorschau und Monatsprognose je Show

### A43 – Produktion und Veröffentlichung konsequent trennen

Separate Aufträge, Zeitpläne, Rechte und Status; interne Produktion und versionierte Freigabe vor Veröffentlichung je Zielkanal.

- **T340:** Getrennte Produktions- und Veröffentlichungsaufträge
- **T341:** Getrennte Verwaltung, Migration und Abnahme
