# PersonalNewsHost v0.1

Kostenfreier Prototyp: RSS-Quellen lesen, kurze deutschsprachige Nachrichtensendung als MP4 mit FFmpeg/eSpeak-NG erstellen und einen Video-RSS-Feed veröffentlichen.

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
- v0.1 nutzt **keine generative Video-KI** und **keinen sprechenden fotorealistischen Avatar**. Optionales Portrait wird als Standbild gezeigt. TTS läuft lokal über eSpeak-NG.
- Die RSS-Zusammenfassung erfolgt regelbasiert (Titel + Feed-Kurzbeschreibung), **nicht** durch eine OpenAI-API. Die ursprüngliche OpenAI-only-Idee ist ohne kostenpflichtige API nicht garantiert umsetzbar.
- Keine fremden Bilder/Videos automatisch übernehmen; Urheberrecht beachten. Die Nachrichten werden nicht unabhängig verifiziert.
- Nur die neueste Ausgabe wird gespeichert, damit das Repository nicht stündlich anwächst.

## Lokal testen (Ubuntu)
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
python3 scripts/generate.py
```

## Dateien
- `config.json`: Quellen und Darstellung
- `scripts/generate.py`: RSS → Text → Sprache → Video → RSS
- `docs/`: GitHub Pages Ausgabe
- `.github/workflows/news.yml`: stündlicher Workflow

## Sicherheit
Keine Zugangsdaten im Repository speichern. RSS-Quellen werden nur über HTTP(S) mit Timeouts gelesen. Für öffentlich sichtbare Inhalte und Bildmaterial ist der Betreiber verantwortlich.
