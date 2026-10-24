# technik

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


## Produktionsversionen

Die Konfiguration enthält `production_version` (Standard: `"1.0"`). Im neuen Tab **Version** kann der Nutzer die Produktionsvariante sehen.

- **1.0 – Minimal:** Die bestehende kostenlose Pipeline ohne kostenpflichtige APIs.
- **2.0 – Erweitert (geplant):** Künftige optionale kostenpflichtige KI-Dienste. Die Auswahl ist absichtlich deaktiviert, solange Pipeline, Provider-Konfiguration, API-Secrets und Kostenlimits noch nicht implementiert sind.

Die Produktionsprüfung lehnt unbekannte oder noch nicht implementierte Versionen ausdrücklich ab, statt stillschweigend kostenpflichtige Dienste zu starten oder auf eine andere Version zurückzufallen. Die bestehende Konfiguration bleibt kompatibel; fehlt `production_version`, wird 1.0 verwendet.

### Vorbereitung für Version 2.0 (ohne kostenpflichtige Aufrufe)

Der Tab **Version** enthält den Konfigurationsentwurf `advanced_services` mit `news_provider`, `voice_provider`, `avatar_provider`, `video_provider`, `max_per_video_eur`, `max_per_month_eur` und `allow_paid`. Alle Budgets sind standardmäßig 0 EUR, `allow_paid` ist `false`. Diese Felder sind **noch keine technisch wirksame Kostenkontrolle**; sie werden von der aktuellen Pipeline nicht verwendet. Version 2.0 bleibt im Auswahlfeld gesperrt und der Produktionsworkflow lehnt sie ab. API-Schlüssel gehören ausschließlich in GitHub Actions Secrets. Eine zukünftige Freischaltung setzt Anbieteradapter, verbindliche Budgetprüfungen, Fehlerbehandlung und Tests voraus.

Die automatische Produktion ist in der ausgelieferten Standardkonfiguration deaktiviert. Manuelle Workflow-Starts bleiben möglich.

### Technische Anbieter-Schnittstellen

`scripts/provider_registry.py` definiert austauschbare Verträge für Nachrichten-, Sprach-, Avatar- und Videodienste. `plan(config)` validiert Anbieter und Euro-Budgets rein lokal, ohne Netzwerkzugriffe oder Gebühren. `require_executable_version(config)` lässt aktuell nur 1.0 zu; 2.0 bleibt auch mit ausdrücklicher Zustimmung gesperrt, solange belastbare Abrechnungskontrollen und Adapter fehlen. Die Produktionsprüfung nutzt dieselbe Validierung.

Tests: `python3 -m unittest discover -s tests`. Der Produktionsworkflow führt diese Tests vor der eigentlichen Verarbeitung aus. Die Provider-Verträge sind eine technische Vorbereitung, noch keine funktionierende kostenpflichtige Pipeline.

### Rechenstandort als Auswahlkriterium

Im Tab **Version** wird vor dem Anbieter zuerst der gewünschte Datenraum (`advanced_services.processing_region`) und optional das Land (`processing_country`) gewählt. `require_verified_region` ist standardmäßig aktiviert. `scripts/processing_location.py` prüft die Konsistenz dieser Angaben; `scripts/provider_registry.py` meldet bei kostenpflichtigen, noch nicht nachgewiesenen Standorten einen zusätzlichen Blockierungsgrund. Die vorhandene Länderliste ist eine begrenzte Auswahlliste, **kein** Verzeichnis tatsächlich verfügbarer Rechenzentren. Anbieter, Produkt, Modell, Unterauftragsverarbeiter, Datenhaltung und grenzüberschreitende Weitergabe müssen vor Freigabe separat anhand belastbarer Anbieterunterlagen geprüft werden. Der Unternehmenssitz ist kein Beleg für Datenresidenz. Bis dahin bleibt 2.0 gesperrt.

### Anbieterkatalog und Standortnachweise

`scripts/provider_catalog.py` enthält je künftigem externen Dienst einen Eintrag mit Verifizierungsstatus, nachgewiesenen Regionen/Ländern, Quellen-URL und Prüfdatum. Derzeit sind **alle externen Einträge unverifiziert**, ohne Quellenangaben; es werden ausdrücklich keine Standortzusagen behauptet. `provider_registry.plan()` wertet die Nachweise je ausgewähltem Dienst aus. Die Konfigurationsseite zeigt die noch offenen Nachweise unmittelbar bei der Anbieterauswahl. Ohne verifizierte Belege blockiert die strikte Standortprüfung externe Anbieter. Selbst bei deaktivierter strikter Prüfung bleibt Version 2.0 aus Sicherheits- und Kostengründen gesperrt. Bevor echte Anbieter freigeschaltet werden, sind produkt-/modellgenaue offizielle Belege, Aktualitätsprüfung und Durchsetzung im Laufzeitadapter erforderlich.

### Recherche zu EU-Verarbeitungsoptionen (22.10.2026)

`docs/provider-research.json` hält öffentlich dokumentierte Bereitstellungsoptionen von Microsoft Foundry (EU Data Zone, regionale Bereitstellung) und Amazon Bedrock (geografisches EU-Inferenzprofil) mit Links auf die Originaldokumentation fest. Diese Optionen sind **keine** verifizierten, in der Laufzeit auswählbaren Provider. Eine EU-Datenzone ist nicht automatisch eine Garantie für ein bestimmtes EU-Mitgliedsland; regionale Verarbeitung muss pro Modell und Deployment geprüft werden. Der Katalog `scripts/provider_catalog.py` bleibt daher für alle externen Anbieter auf `unverified`. Die Recherche ist auch im Tab Version verlinkt.

### Modell- und Endpunktprüfung (noch ohne Freigaben)

`docs/provider-research.json` verlangt jetzt für jeden Kandidaten die Modell-ID, Deployment-Typ, Ausgangs- und Zielregionen, Angaben zu Datenaufbewahrung und Unterauftragsverarbeitern sowie offizielle Quelle und Prüfdatum. `scripts/model_residency.py` prüft offline die Vollständigkeit und die Übereinstimmung der angegebenen Zielregionen mit einer erlaubten Region-Liste. Diese Plausibilitätsprüfung **beweist nicht**, dass ein Dienst tatsächlich dort rechnet, und setzt `approved` daher stets auf `false`. Die AWS-Dokumentation fordert `GetInferenceProfile` für jede Ausgangsregion; Microsoft weist auf die modellabhängige Verfügbarkeit der Deployment-Typen hin. Die Konfiguration aktiviert weiterhin keine externen Dienste. Tests: `python3 -m unittest discover -s tests`.

### Standort-Recherche offline prüfen

Mit `python3 -m scripts.audit_provider_research` lässt sich der öffentliche Recherchekatalog lokal auf fehlende modellgenaue Nachweise prüfen. Der Befehl benötigt keine Zugangsdaten, ruft keine Provider-APIs auf und erzeugt keine Kosten. Das Ergebnis ist ein **Recherchebericht**, keine Live-Verfügbarkeitsprüfung und keine Anbieterfreigabe. Für eine tatsächliche Prüfung bei AWS oder Microsoft werden später konkrete Modell-IDs, Regionen, Endpunkte und gegebenenfalls Kontoberechtigungen benötigt. Bis dahin bleiben alle externen Anbieter gesperrt.

### Standort-Prüfstatus in der Konfiguration

Im Tab **Version** liest die Konfigurationsseite `docs/provider-research.json` und zeigt je recherchierter Anbieteroption die fehlenden Pflichtangaben an. Der Button **Prüfdaten aktualisieren** lädt die JSON-Datei erneut. Es erfolgt keine externe Anbieter-API-Abfrage; der Browser liest nur die öffentliche Datei der eigenen GitHub-Pages-Seite. Die Anzeige ist eine dokumentarische Vollständigkeitsprüfung und kein Nachweis einer tatsächlichen Datenresidenz oder Modellverfügbarkeit. Alle externen Optionen bleiben nicht freigegeben.

### Anbieterfilter nach Standort und Nachweisstatus

Der Recherchebereich im Tab **Version** kann nach Verarbeitungsraum, Land, Dienst und Nachweisstatus gefiltert werden. Ein geografischer Treffer wird **nur** angezeigt, wenn der Katalog ausdrücklich `verification_status: verified`, `model_verified: true` und passende `verified_regions` bzw. `verified_countries` enthält. Die bislang unverifizierten Kandidaten erscheinen daher bei Länder-/Regionsfiltern bewusst nicht. Filterung ist keine technische Freigabe; die 2.0-Ausführung bleibt gesperrt. Die angezeigten Treffer beruhen ausschließlich auf Katalogeinträgen, nicht auf einer Live-Prüfung.

### Standortauswahl mit Symbolen

Im Tab **Version** stehen die Kontinent-/Datenraumliste mit Globussymbolen und die Länderliste mit Flaggen nebeneinander (mobil untereinander). Ein Wechsel des Kontinents blendet unpassende Länder aus und entfernt eine eventuell nicht mehr passende Länderauswahl. Kontinent und Land werden automatisch in die Filter der Anbieterrecherche übernommen; dort erscheinen weiterhin nur nachgewiesene Standorte. Die gespeicherten Konfigurationswerte (`processing_region`, `processing_country`) und die Sperre für Version 2.0 bleiben unverändert.

### Version 2.0 als vierstufige Reiteransicht

Im Reiter **Version** besitzt der Bereich **Version 2.0 vorbereiten** vier Unterreiter: **Rechenstandort**, **Dienste**, **Standortnachweis** und **Kostenobergrenzen**. Zwischen ihnen kann per Reiter, Tastatur (Pfeiltasten, Pos1/Ende) oder **Zurück/Weiter** navigiert werden. Eine Fortschrittsanzeige benennt den aktuellen Schritt. Die Felder bleiben im Formular und werden nicht beim Reiterwechsel zurückgesetzt. Diese Bedienoberfläche aktiviert Version 2.0 nicht und führt keine kostenpflichtigen Anfragen aus.

### Abgleich der Konfiguration mit der Produktion

Der produktive Generator berücksichtigt `tts_engine` mit den Werten `piper` (mit eSpeak-Fallback) und `espeak`. Die bisherige Weboberfläche bietet für diese Auswahl noch kein Feld. `presenter_settings.voice_model` ist weiterhin nicht frei auswählbar, da der GitHub-Workflow nur `de_DE-thorsten-high` herunterlädt. `intro_mode`, `intro_static_type`, `intro_static_color` und `intro_static_image` sind derzeit noch nicht vollständig mit dem produktiven FFmpeg-Generator verbunden. Lippensynchronisation bleibt experimentell; externe KI-Dienste und wirksame Kostenlimits bleiben gesperrt. Nicht implementierte Funktionen dürfen nicht als produktiv beworben werden.

### Weitere Konfigurationsfunktionen (22.10.2026)

Die Produktivkette wertet jetzt `tts_engine` (`piper` oder `espeak`) aus; die Web-Konfiguration kann diesen Wert bearbeiten und speichern. Der FFmpeg-Generator berücksichtigt nun auch `presenter_settings.scenes.intro_mode=static` mit `intro_static_type=color` oder `image`, `intro_static_color` und `intro_static_image`. Das Portrait bleibt im statischen Intro ausgeblendet und kann im Outro erscheinen. Diese neuen Änderungen sind eingecheckt, aber ein vollständiger produktiver FFmpeg-Testlauf steht noch aus. Weitere Modellwahl und Lippensynchronisation sind nicht produktiv verfügbar.
