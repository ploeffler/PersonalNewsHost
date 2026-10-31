# Abnahme 0.1 – Fundament und Nachrichtenauswahl

Stand: 29.10.2026. Branch **Full-featured-Newsoutlet**. Version 0.1 ist ein Entwicklungsmeilenstein, keine Freigabe der später geplanten unbeaufsichtigten Gesamtproduktion. `main` wird nicht geändert. Umfang: die 14 Aufgaben der Version 0.1, nicht die gesamte Roadmap.

| Aufgabe | Nachweis / abgenommener Umfang |
|---|---|
| T001 | [Inventar](inventar-0.1.md): sämtliche Skripte, Konfigurationsschlüssel, Workflows samt Triggern/Timeouts, Tests, externe Datenflüsse und PR-Integration dokumentiert. Unausgeführte GPU-Experimente erhalten keine erfundenen Laufzeiten. |
| T002 | JSON-Schema und CLI; beide Basiskonfigurationen plus Showbeispiel gültig; ungültige Konfiguration stoppt vor RSS und Rendering. |
| T010 | Alte Konfiguration als `main`; zwei Showvideos mit getrennten Ausgabepfaden im FFmpeg-Fixturetest; Vererbung und Fehlerwiederherstellung geprüft. |
| T011 | Feedrubrik und Showfilter; Kategorie im Beitragsmodell; unbekannte Zuordnung `general`; KI-Neuzuordnung bleibt optional/inaktiv. |
| T012 | Konservatives Ereignisclustering; korrigierte Worterkennung; positive Mehrquellen- und negative Trennungsfixtures; sämtliche Quellen bleiben im Beitragsmodell. |
| T052 | Domänen-/Stichwortsperren, Quellengewichtung in RSS- und gespeichertem Redaktionspfad. Nicht zulässige vorbereitete Gruppen werden vollständig ausgeschlossen. |
| T072 | Offline-Testläufer, Python-Lint, lokale Linkprüfung und JavaScript-Verträge in PR-/Branch-CI. |
| T073 | Secret-Scan, credentialfreie Feed-URLs, Datenhinweis/Impressumsvorlage, unveränderliche Action-SHAs und exakte direkte Python-Constraints. Kein vollständiger transitiver Lock aller GPU-Prototypen behauptet. |
| T100 | Konfigurierbare Registry für sechs Arten, deaktiviert als Standard; ausschließlich deterministische Mockadapter aktivierbar. Inferenzprovider laufen durch die gemeinsame Runtime. RSS-/Medienabrufe bleiben getrennte Quellenbeschaffung. |
| T101 | Dauerhafte SQLite-Vorabreservierungen, Kosten- und Einheitenlimit, Rate-Limit, explizites Opt-in, Fallback und Report. Konkurrenz, Neustart und Monatswechsel geprüft. Nur Mockkosten, keine echte Anbieterabrechnung. |
| T103 | Cache über Provider, Modell, Aufgabe, Prompt-/Providerrevision, Eingabe, Namespace und Schema; parallele gleiche Anfrage einmal ausgeführt; Actions-Zustand wird wiederverwendet. |
| T104 | Allowlist skalarer Payloadfelder, bekannte Secretmuster plus konfigurierte Secretwerte, Audit nur mit ID/Aufgabe/Umfang/Zeit. |
| T130 | Strikte Schemata für Zusammenfassung, Entitäten, Klassifikation, Relevanz, Bias-Hinweis, Duplikatkandidaten und Überschrift. Baselines liefern ausdrücklich keine erfundene Bewertung. |
| T135 | Feedtext ist Datenmaterial, keine ausführbare Instruktion. Task/Schema/Tools können durch Payload nicht umgeschaltet werden; Schemawidrige Antworten werden abgelehnt. Kein echter LLM-Adapter in 0.1; daraus folgt keine generelle Sicherheitsgarantie für spätere Modelle. |

## Prüfungen

- Gesamtsuite vor abschließenden Dokumentations-/Prüfläuferergänzungen: **222 Tests, erfolgreich, 36,967 Sekunden** mit gesperrten Python-Netzwerkzugriffen.
- Abschließender Teststand und GitHub-CI werden beim Release in `planning/fortschritt.yaml` festgehalten.
- Ruff `F821,F822,F823` für sämtliche Skripte und Tests: erfolgreich.
- Beide Konfigurationen und Mehrshowbeispiel schema-valide.
- JavaScript-Unitprüfungen: Feed-Picker, Nachrichtenübersicht, Playlist; JS-/CJS-Syntaxprüfung.
- Workflow-YAML und sämtliche verwendeten Action-Commit-SHAs geprüft; Referenzsnapshot in `planning/action-pins.json`.
- Keine realen Provider-, Telegram- oder Veröffentlichungstests ausgelöst. Videotests verwenden lokale Fixtures und synthetische Audiodateien.

## Grenzen des Meilensteins

Die neue Provideranalyse ist optional und verändert keine bereits freigegebene Sprecherformulierung. Für Bild, Video, Avatar und TTS liefern Provider-Mocks ausschließlich gekennzeichnete Testreferenzen, keine realen Medien. Die bisherige lokale Produktionspipeline bleibt verfügbar; generative Medienadapter folgen später. Es sind keine kommerziellen Adapter enthalten.

Kosten sind konservative Mockreservierungen, keine Rechnungen. Bei fehlgeschlagenen oder unklaren Versuchen wird die Reservierung nicht freigegeben. Ein echter kostenpflichtiger Adapter benötigt zusätzlich einen überprüften Kostenhöchstwert und eine verbindliche zentrale Verbrauchspersistenz; ein best-effort Actions-Cache genügt dafür nicht. Der lokale Ledger ist dauerhaft, Actions-Zustand dient hier nur Mock-/Cachewiederverwendung.

Die neue Showausgabe ist intern. HTTPS-Adminverwaltung, CMS, vollständige Publikationswarteschlange, verpflichtende AI-/Datumsarchiv-Finalisierung und Studio-/Avatarwizards liegen in späteren Versionen. Der vorhandene Altgenerator veröffentlicht weiterhin nach seinem bisherigen Verhalten; das ist keine neue Freigabe des geplanten Gesamtsystems. Direkte Showproduktion erfolgt ausdrücklich über `produce_show.py`.

Vollständige Anleitung: [Shows](shows.md), [Providerbetrieb](provider-runtime.md), [Datenschutz](datenschutz.md).
