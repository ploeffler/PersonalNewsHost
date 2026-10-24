# konfiguration

## Konfiguration in Forks und Datenschutz

**Achtung: Anders als GitHub Actions Secrets wird `config.json` beim Forken mitkopiert.** Die Datei und `docs/config.json` sind öffentlich einsehbar. Sie dürfen keine Tokens, Passwörter, privaten Empfängerkennungen oder andere vertrauliche Daten enthalten.

Für neue Installationen steht die neutrale Vorlage [`config.example.json`](config.example.json) bereit. Nach dem Forken die eigene `config.json` durch eine Kopie dieser Vorlage ersetzen, persönliche RSS-Feeds und Einstellungen hinzufügen und erst dann die Produktion aktivieren. Die neutrale Vorlage hat keine voreingestellten RSS-Feeds und deaktiviert Telegram sowie die Automatik. Eigene Zugangsdaten ausschließlich als GitHub Actions Secrets des jeweiligen Forks hinterlegen.

**Wichtig:** Das Ersetzen der Datei im Fork entfernt alte Inhalte nicht aus der Git-Historie. Eine öffentliche Repository-Konfiguration ist daher kein geeigneter Ort für Geheimnisse. Die Konfigurations-Webseite speichert weiterhin im öffentlichen Repository; diese Speicherung ist **nicht privat**. Eine automatische Isolation der gesamten Konfiguration zwischen Original und Fork ist noch nicht umgesetzt. Der Schutz der Telegram-Secrets bleibt davon unabhängig gewährleistet.

# PersonalNewsHost

**Experimentelles, automatisiertes RSS-Nachrichtenstudio – ohne kostenpflichtige APIs oder eigenen Server.**

PersonalNewsHost liest konfigurierbare RSS-Feeds und erzeugt deutschsprachige Nachrichtenvideos. Die derzeitige **Produktivversion** veröffentlicht regelmäßig ein MP4 mit Piper-Sprachausgabe, einer Webseite und einem Video-RSS-Feed über GitHub Pages. Daneben entsteht ein **separater, noch nicht veröffentlichender Testzweig der Verarbeitung** mit Themen-Clustering, parallelen Videosegmenten und einem lippensynchronen Moderator auf Basis von MuseTalk.

> **Projektziel:** Möglichst stündlich eine automatisch erzeugte Nachrichtensendung, konfigurierbare Quellen, Moderatorenportrait und Studiokulisse, Video-RSS und **0 € monatliche Zusatzkosten**. Die Umsetzung ist ein Prototyp, kein redaktionell verifiziertes Nachrichtensystem. Die GitHub-Freikontingente und Nutzungsbedingungen müssen eingehalten werden.


## Direktes Speichern der Web-Konfiguration (Beta)

Unter [settings.html](https://ploeffler.github.io/PersonalNewsHost/settings.html) gibt es neben dem JSON-Download jetzt **Direkt auf GitHub speichern**. Hierfür kann der Repository-Eigentümer einen [Fine-grained Personal Access Token](https://github.com/settings/personal-access-tokens/new) erzeugen, ausschließlich für `ploeffler/PersonalNewsHost`, mit `Contents: Read and write`. Token nur auf der vertrauenswürdigen GitHub-Pages-Projektseite eingeben; nicht in GitHub-Dateien, Screenshots, Issues oder Chats veröffentlichen. Die Webseite speichert den Token nicht dauerhaft und leert das Feld nach dem Versuch. Die GitHub-API aktualisiert `config.json` auf `main` mit dem aktuellen Datei-SHA, damit Konflikte nicht still überschrieben werden. Die alte Download-/Import-Möglichkeit bleibt erhalten. GitHub Pages lädt bevorzugt die veröffentlichte `docs/config.json` und fällt bei Fehlern auf die eingebettete Konfiguration zurück.

**Wichtig:** Dies ist eine erste Implementierung und noch nicht im Browser mit einem echten Token getestet. Änderungen wirken erst nach einem folgenden Produktionslauf. Eine sichere OAuth-Anmeldung ohne manuell erstellten Token und das Hochladen von Bilddateien stehen noch aus.


## Web-Konfiguration (erste Beta)

Die erste browserbasierte Oberfläche ist unter **[Konfiguration öffnen](https://ploeffler.github.io/PersonalNewsHost/settings.html)** erreichbar. Sie ist als statische GitHub-Pages-Seite umgesetzt und benötigt keinen eigenen Server.

Derzeit kann man RSS-Quellen, Titel, Meldungsanzahl, Textlänge, Piper-Sprechtempo und Stimmlage, Moderatorenname, Portrait- und Hintergrundpfad sowie Szeneneinstellungen bearbeiten. Die Seite lädt die öffentliche `config.json` aus dem Repository, validiert Eingaben und bietet den Download einer aktualisierten `config.json` an. Alternativ lässt sich eine vorhandene JSON-Datei importieren.

**Noch nicht umgesetzt:** Automatisches Zurückschreiben der Konfiguration nach GitHub, Upload von Bilddateien, sichere Anmeldung und Start eines Workflows direkt aus der Oberfläche. Die heruntergeladene `config.json` muss derzeit manuell ins Repository übernommen werden. **Keine GitHub-Tokens oder Passwörter in diese Webseite eingeben.**

Damit ist ein erster Teil des v1.0-Ziels vorhanden; die vollständige browserbasierte Administration steht noch aus.

### Stimmlage anpassen

Die Sprecherstimme lässt sich unabhängig vom Sprechtempo über `voice_pitch_semitones` in `config.json` verändern. Der aktuelle Testwert ist **−1,5 Halbtöne** (tiefer); `0` bedeutet unveränderte Tonhöhe. Die Web-Konfiguration erlaubt Werte von −6 bis +6 Halbtönen. FFmpeg verschiebt die Tonhöhe nach der Piper-Synthese und gleicht die Wiedergabegeschwindigkeit aus. Dadurch bleibt das eingestellte Piper-Sprechtempo grundsätzlich erhalten, bei größeren Änderungen können allerdings Klangartefakte entstehen.

**Status:** Implementiert, aber noch nicht durch einen neuen vollständigen GitHub-Actions-Lauf geprüft.

### Intro und Outro anpassen

In der Web-Konfiguration stehen jetzt weitere Szenenoptionen zur Verfügung:

- **Intro-Darstellung:** `Avatar` (MuseTalk-Lippenanimation) oder `Statischer Hintergrund` (ohne Avatar). Bei statischem Intro kann zwischen **einfärbigem Hintergrund mit frei wählbarer Farbe** und **einer Bilddatei** gewählt werden. Ein Bild muss bereits im Repository liegen.
- **Intro-Text:** frei editierbarer Sprechertext. Der Platzhalter `{title}` wird durch den konfigurierten Sendungstitel ersetzt.
- **Outro-Text:** ebenfalls frei editierbarer Sprechertext.

Die Optionen werden in `config.json` unter `presenter_settings.scenes.intro_mode`, `intro_text` und `outro_text` sowie `intro_static_type`, `intro_static_color` und `intro_static_image` gespeichert. Der experimentelle Sendungsplan und sein Renderer berücksichtigen diese Einstellungen. Das **Outro verwendet weiterhin den Avatar**; die Auswahl zwischen Avatar und Standbild betrifft zunächst nur das Intro. Ein eigener Hintergrund unter `assets/background.jpg` muss vorhanden sein, wenn statt der technischen Ersatzfarbe ein individuelles Standbild erscheinen soll.

**Status:** Code umgesetzt, aber noch nicht durch einen neuen vollständigen Workflow-Lauf bestätigt. Der bisherige stündliche Produktivgenerator übernimmt diese neuen Texte und die Intro-Moduswahl noch nicht; das folgt bei der Integration der neuen Pipeline.


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


## Automatik / Produktionsintervall

Der Tab **Automatik** auf der Web-Konfigurationsseite steuert `automation` in `config.json`:

- `enabled`: automatische Produktion ein-/ausschalten (manuelle Starts bleiben möglich).
- `interval_hours`: 1, 2, 3, 4, 6, 8, 12 oder 24 Stunden.
- `start_hour_utc`: Stundenraster in UTC (0–23).
- `days`: `daily`, `weekdays` oder `weekends`.

Der GitHub-Actions-Cron bleibt technisch auf **stündlich, Minute 17 UTC** eingestellt. Ein kurzer Prüfjob überspringt alle rechenintensiven Schritte, wenn der gewählte Termin nicht fällig ist. So funktioniert die Konfiguration in eigenen Forks ohne GitHub-Workflow-Bearbeitung. Die GitHub-Actions-Ausführung ist **nicht minutengenau garantiert** und kann verzögert oder ausgelassen werden. Zeitangaben sind UTC; lokale Sommer-/Winterzeit wird nicht automatisch umgerechnet. Für das Aktivieren der geplanten Workflows im eigenen Fork gelten die GitHub-Einstellungen des Forks.

### Zeitzonen und Sommerzeit

Im Tab **Automatik** kann eine IANA-Zeitzone (z. B. `Europe/Vienna`) gewählt werden. `automation.timezone` und `automation.start_hour_local` steuern das lokale Stundenraster. Ältere Konfigurationen mit `start_hour_utc` funktionieren weiterhin und verwenden standardmäßig UTC. Die Umstellung auf Sommer-/Winterzeit erfolgt automatisch. Doppelt vorkommende Stunden im Herbst werden nur einmal ausgeführt; nicht vorhandene Stunden im Frühjahr entfallen. Der GitHub-Actions-Cron bleibt stündlich und kann verspätet laufen.

