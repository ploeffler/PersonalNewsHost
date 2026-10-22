# PersonalNewsHost

**Experimentelles, automatisiertes RSS-Nachrichtenstudio – ohne kostenpflichtige APIs oder eigenen Server.**

PersonalNewsHost liest konfigurierbare RSS-Feeds und erzeugt deutschsprachige Nachrichtenvideos. Die derzeitige **Produktivversion** veröffentlicht regelmäßig ein MP4 mit Piper-Sprachausgabe, einer Webseite und einem Video-RSS-Feed über GitHub Pages. Daneben entsteht ein **separater, noch nicht veröffentlichender Testzweig der Verarbeitung** mit Themen-Clustering, parallelen Videosegmenten und einem lippensynchronen Moderator auf Basis von MuseTalk.

> **Projektziel:** Möglichst stündlich eine automatisch erzeugte Nachrichtensendung, konfigurierbare Quellen, Moderatorenportrait und Studiokulisse, Video-RSS und **0 € monatliche Zusatzkosten**. Die Umsetzung ist ein Prototyp, kein redaktionell verifiziertes Nachrichtensystem. Die GitHub-Freikontingente und Nutzungsbedingungen müssen eingehalten werden.

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

## Nächste Entwicklungsschritte

1. Den vollständigen MuseTalk-Workflow mit neuem Sprechtempo, Nachrichtentafeln und aktualisierten Actions testen.
2. Für die Nachrichtenbeiträge rechtlich nutzbare Bilder und bessere Szenenübergänge ergänzen.
3. Themenauswahl und redaktionelle Prüfung verbessern.
4. Erst nach Qualitätstests eine kontrollierte Übernahme der experimentellen Pipeline in die stündliche Veröffentlichung vorsehen.
