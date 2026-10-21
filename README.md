# PersonalNewsHost v0.4

Kostenfreier Prototyp: RSS-Quellen lesen, kurze deutschsprachige Nachrichtensendung als MP4 mit FFmpeg/Piper (eSpeak-NG als Fallback) erstellen und einen Video-RSS-Feed veröffentlichen.

## Einrichtung
1. Unter **Settings → Pages** die Quelle **Deploy from a branch**, Branch **main**, Ordner **/docs** auswählen.
2. Unter **Actions** den Workflow **Generate news video** manuell starten; danach ist ein stündlicher Lauf (best effort) geplant.
3. In `config.json` RSS-Quellen, Titel, Sprecherstimme und Dateinamen anpassen.
4. Eigene Dateien optional unter `assets/background.jpg` und `assets/presenter.png` ablegen (nur Material mit Nutzungsrechten).

Website: https://ploeffler.github.io/PersonalNewsHost/
Video-RSS: https://ploeffler.github.io/PersonalNewsHost/feed.xml

## Technische Grenzen
- 0 € zusätzliche Kosten bei Nutzung der kostenlosen GitHub-Kontingente, solange deren Grenzen eingehalten werden; GitHub Actions und Pages haben Limits und Bedingungen.
- GitHub Actions Cron ist **nicht garantiert minutengenau** und kann Läufe auslassen.
- v0.4 nutzt **keine generative Video-KI** und **keinen sprechenden fotorealistischen Avatar**. Optionales Portrait wird als Standbild gezeigt. TTS läuft lokal mit dem neuronalen Piper-Modell de_DE-thorsten-high, sofern der Download gelingt; sonst eSpeak-NG.
- Die RSS-Zusammenfassung erfolgt regelbasiert (Titel + Feed-Kurzbeschreibung), **nicht** durch eine OpenAI-API. Die ursprüngliche OpenAI-only-Idee ist ohne kostenpflichtige API nicht garantiert umsetzbar.
- Keine fremden Bilder/Videos automatisch übernehmen; Urheberrecht beachten. Die Nachrichten werden nicht unabhängig verifiziert.
- Nur die neueste Ausgabe wird gespeichert, damit das Repository nicht stündlich anwächst.

## Lokal testen (Ubuntu)
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
python3 -m pip install piper-tts
# Ohne heruntergeladenes Piper-Modell wird automatisch eSpeak-NG verwendet.
python3 scripts/generate.py
```

## Dateien
- `config.json`: Quellen und Darstellung
- `scripts/generate.py`: RSS → Text → Sprache → Video → RSS
- `docs/`: GitHub Pages Ausgabe
- `.github/workflows/news.yml`: stündlicher Workflow

## Sicherheit
Keine Zugangsdaten im Repository speichern. RSS-Quellen werden nur über HTTP(S) mit Timeouts gelesen. Für öffentlich sichtbare Inhalte und Bildmaterial ist der Betreiber verantwortlich.

## v0.4 – Natürlichere deutsche Stimme
GitHub Actions installiert Piper TTS und lädt beim Lauf das frei verfügbare deutsche Modell `de_DE-thorsten-high` samt Konfiguration von `rhasspy/piper-voices` (Hugging Face). Das Modell wird nicht im Repository gespeichert. Schlägt Download oder Synthese fehl, bleibt die bisherige eSpeak-NG-Stimme als Fallback erhalten. Die Nutzungsbedingungen und Lizenzhinweise des jeweiligen Modells sind vor Weiterverbreitung zu prüfen. Kein kostenpflichtiger API-Aufruf.

## v0.4 – Sprechqualität
Hochauflösendes Thorsten-Modell, einstellbare Sprechgeschwindigkeit (`piper_length_scale`), zusätzliche Satzpausen. Bei fehlendem Modell bleibt eSpeak als Fallback erhalten. Das größere Modell kann die Laufzeit erhöhen.

## v0.4 – Konfigurierbarer Moderator (Vorbereitung)
Unter `presenter_settings` in `config.json` lassen sich Name, Geschlecht (Metadaten), Portraitdatei, Hintergrund, Stimmmodell (derzeit nur Thorsten High installiert) und die geplante Lippen-Synchronisation konfigurieren. Das Portrait ist ein selbst hochgeladenes PNG unter `assets/presenter.png`. `lip_sync.enabled` bleibt **false**: Ein echtes Lippen-Synchronisationsmodell ist noch nicht integriert und wird ausdrücklich nicht als funktionierend ausgegeben. Selbst wenn der Schalter auf true gesetzt wird, wird derzeit nur das statische Portrait verwendet und ein Hinweis im Workflow protokolliert. Vor der Integration sind CPU-Laufzeit, Modelllizenzen und GitHub-Actions-Limits zu testen.

## Szenensteuerung
`presenter_settings.scenes.intro_seconds` und `outro_seconds` steuern die Moderator-Einblendungen; im Mittelteil zeigt FFmpeg automatisch eine Schlagzeilentafel, falls `show_headlines` aktiviert ist. Ohne hochgeladenes Portrait bleibt das Studio sichtbar. Audio läuft kontinuierlich. Es gibt **noch keine** echten Lippenbewegungen oder automatischen externen Nachrichtenbilder. Nach jeder Konfigurationsänderung den Workflow testen.
