# Repository-Installation unter Linux

Entwicklungsstand T181 / 0.2. Erster Abnahmeumfang: **Ubuntu 24.04 LTS, x86_64,
Python 3.12**, CPU-Basis mit eSpeak-NG. Andere Distributionen, Architekturen und
Pythonversionen werden von diesem Installer noch nicht als geprüft angenommen.
Der aktuelle Entwicklungsrechner mit Ubuntu 26.04/Python 3.14 liegt außerhalb
dieses Abnahmeumfangs; dort wurden keine Systempakete installiert.

## 1. Systemvoraussetzungen bewusst installieren

Auf dem vorgesehenen Ubuntu-24.04-Rechner mit passenden Administratorrechten:

```bash
sudo apt-get update
sudo apt-get install git python3-venv ffmpeg espeak-ng fonts-dejavu-core
```

Der Installer führt selbst kein sudo/apt und keine globalen pip-Installationen aus.
Offizielle Paketquellen: [FFmpeg](https://packages.ubuntu.com/noble/ffmpeg),
[eSpeak-NG](https://packages.ubuntu.com/noble/espeak-ng).

## 2. Repository in einen neuen Ordner klonen

```bash
git clone --branch Full-featured-Newsoutlet https://github.com/ploeffler/PersonalNewsHost.git personalnewshost
cd personalnewshost
git rev-parse HEAD
```

Den Commit zur Reproduzierbarkeit notieren. Der Entwicklungsbranch ist veränderlich;
eine neue Version nicht ungeprüft über eigene Änderungen ziehen. Wer im eigenen
Fork arbeitet, ersetzt die URL durch die eigene Fork-URL; der gewählte Branch
muss im Fork vorhanden sein. Es wird kein bestehender Ordner zurückgesetzt.
GitHub Actions oder GitHub Secrets sind für lokalen Kernbetrieb nicht nötig.

## 3. Vorprüfen und lokale Umgebung installieren

```bash
python3 scripts/install_linux.py
python3 scripts/install_linux.py --install
```

Ohne Flag zeigt der Befehl nur Plattform, fehlende Programme und den Installations-
hinweis; er verändert keine Dateien. `--install` legt ausschließlich die eigene
`.venv-pnh` an, installiert das gepinnte Kernprofil plus Pillow und validiert
`config.json`. Es werden keine Cloud-SDKs, GPUs, KI-Modelle oder Dienste eingerichtet.
Pythonpakete werden aus den konfigurierten Paketquellen geladen; Netzwerkzugang
ist für die erste Installation nötig. Die Pythonumgebung ist nicht verschiebbar,
siehe [Python-venv-Dokumentation](https://docs.python.org/3.12/library/venv.html).

Ist `config.json` schon vorhanden, bleibt sie bytegleich erhalten. Nur wenn sie
fehlt, wird `config.example.json` exklusiv als neue private Datei kopiert. Eine
ungültige vorhandene Konfiguration führt zum Abbruch, nicht zum Überschreiben.
Modelle, Assets, Secrets, Archive und bestehender Zustand bleiben erhalten.
Neu benötigte Datenverzeichnisse werden angelegt, niemals bereinigt.

Wiederholen ist vorgesehen: passen Requirements-Fingerprint und Imports, entfällt
pip. Bei geänderten Requirements werden nur Pakete in der verwalteten Umgebung
aktualisiert. Eine fremde `.venv-pnh` ohne Verwaltungsmarker oder ein Symlinkziel
wird nicht verändert. Ein gescheiterter Aufbau kann im eigenen markierten
Verzeichnis erneut versucht werden. Den Installer nicht parallel zu einem
laufenden Dienst als Ersatz für den künftigen sicheren Updater verwenden.

Ergebnis: privater Status `state/install/install.json`. Die bestehende `.venv`
und die getrennten experimentellen Reel-Umgebungen bleiben unberührt.

## 4. Sprache und Medien prüfen

```bash
.venv-pnh/bin/python scripts/local_runtime.py inspect
.venv-pnh/bin/python scripts/validate_config.py config.json
```

eSpeak-NG bildet das getestete CPU-Basisprofil; für eine bewusste Auswahl
`tts_engine` auf `espeak` setzen. Der Installer ändert eine vorhandene Sprachwahl
nicht. Piper benötigt die getrennt einzurichtende Stimme und Modellkonfiguration;
siehe [Provider einrichten](provider-einrichtung.md). Assets stammen aus der
notierten Repositoryrevision. Modelle werden weder ungeprüft nachgeladen noch
vorhandene Gewichte ersetzt. Bei anderer Lizenz oder eigenen Medien bewusst
passende Dateien konfigurieren. Fehlende optionale Bilder können den vorhandenen
neutralen Renderfallback auslösen.

## 5. Sendung erzeugen und lokal ansehen

```bash
.venv-pnh/bin/python scripts/local_runtime.py produce --show main
```

Die Basiskonfiguration ohne explizite Shows heißt `main`. Eigene Feeds erfordern
Internet und passende Nutzungsrechte. Produktion liegt unter
`out/productions/main`; es gibt keinen automatischen Telegram-/Cloudversand.
Nur nach bewusster Sichtung öffentliche Dateien für `out/public` bereitstellen.
Vorhandene öffentliche Dateien nicht pauschal überschreiben.

```bash
.venv-pnh/bin/python scripts/local_runtime.py serve-preview --port 8080
```

Der zweite Befehl liefert nur `out/public` über `http://127.0.0.1:8080` aus.
Das ist eine lokale Vorschau, kein öffentlicher HTTPS-/Adminbetrieb. systemd,
Scheduler und TLS folgen mit ihren eigenen Aufgaben. Details:
[Betriebsvertrag](runtime-vertrag.md).

## Abnahme und Fehler

Der Workflow „Linux installation smoke“ installiert auf einem frischen
Ubuntu-24.04-Runner. Er wiederholt die Installation mit Prüfdaten in Zustand,
Modellen und Archiv, prüft den Konfigurationserhalt, rendert einen lokalen
Fixturefeed mit echter eSpeak-Stimme und ruft Seite und Video über Loopback ab.
Testausgaben werden danach entfernt; bestehende Benutzerproduktionen werden
nicht als Testziele verwendet. Die automatische Abnahme ist keine Portainer-
oder Dockerinstallation.

`preflight_failed`: Plattform, Python und genannte Programme prüfen.
`existing_environment_not_managed`: fremde Umgebung erhalten und ihren Ursprung
klären, nicht automatisch löschen. `environment_identity_mismatch`: falscher
Interpreter/verschobene Umgebung. `environment_or_dependency_setup_failed`:
venv-Unterstützung, Paketquellen, Netzwerk und freie Kapazität prüfen. Private
Proxy-/Registryantworten werden nicht in Fehlermeldungen übernommen.
