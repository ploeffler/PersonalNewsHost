# betrieb und sicherheit

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


## Kosten, Grenzen und Verantwortung

- **0 € ist ein Ziel unter Bedingungen, keine Kosten- oder Verfügbarkeitsgarantie.** GitHub Actions und GitHub Pages unterliegen Kontingenten, Nutzungsregeln und möglichen Änderungen. Besonders CPU-lastige MuseTalk-Tests können viel Actions-Laufzeit verbrauchen.
- Keine kostenpflichtige OpenAI-API ist in den aktuellen Workflows eingebunden. Die Texte werden regelbasiert aus RSS-Metadaten erstellt; dies ist **keine** KI-gestützte Recherche oder unabhängige Faktenprüfung.
- Automatische Übernahme fremder Fotos oder Videos ist nicht implementiert. Für Portraits, Bilder, Audio, RSS-Inhalte und verwendete Modelle sind Urheber-, Persönlichkeits- und Lizenzrechte zu prüfen.
- Keine Zugangsdaten in `config.json` oder das öffentliche Repository schreiben. RSS-Inhalte sind fremde, nicht vertrauenswürdige Eingaben.
- Für Inhalt, sachliche Richtigkeit und Veröffentlichung der Sendung bleibt der Betreiber verantwortlich.


## Telegram für eigene Forks (optional)

**Sicherheit bei Forks:** GitHub kopiert beim Forken **keine Repository- oder Actions-Secrets**. Ein Fork kann deshalb weder den Bot-Token noch die Chat-ID des ursprünglichen PersonalNewsHost-Repositories lesen oder verwenden. `${{ secrets.TELEGRAM_BOT_TOKEN }}` und `${{ secrets.TELEGRAM_CHAT_ID }}` beziehen sich immer auf die Secrets des Repositories, in dem der Workflow läuft. Ohne eigene Secrets ist der Telegram-Versand nicht möglich; bei aktivierter Telegram-Option meldet der Versand einen Fehler, ohne die Website-Veröffentlichung rückgängig zu machen. Jeder Fork-Betreiber benötigt einen **eigenen Bot-Token und ein eigenes Ziel**. Es gibt keine gemeinsamen oder fest im Quellcode hinterlegten Telegram-Zugangsdaten.

**Schutz des Originalprojekts:** Tokens niemals in `config.json`, Workflow-Dateien, Commits, Issues, Pull Requests, Screenshots oder Logs eintragen. Ausschließlich **Settings → Secrets and variables → Actions** verwenden. GitHub-Secrets werden zwar in Logs nach Möglichkeit maskiert, aber die Maskierung ist keine vollständige Sicherheitsgrenze. Wer Schreibzugriff auf Workflows im Originalrepository hat, kann potenziell dessen Secrets missbrauchen; deshalb Schreibrechte und Workflow-Änderungen streng begrenzen. Bei Verdacht auf Offenlegung den Token über BotFather widerrufen und ersetzen.

**Telegram-Ablaufzeit:** Gesendete Telegram-Nachrichten werden nach frühestens 25 Stunden durch den separaten stündlichen Workflow `telegram-cleanup.yml` gelöscht. GitHub-Actions-Verzögerungen können die Löschung verschieben. Die Löschung betrifft nicht die MP4-Datei auf GitHub Pages und nicht den Video-RSS-Feed. Die automatische Löschung benötigt dieselben **fork-eigenen** Secrets. Ein erfolgreicher End-to-End-Test mit einem echten Bot steht noch aus.

Jeder Fork kann Telegram unabhängig aktivieren. In der Web-Konfiguration unter „Telegram-Veröffentlichung“ sind Empfängerart (Kanal, privater Chat, Gruppe) und Versandart (automatisch, nur Video, nur Link) wählbar. Standardmäßig ist Telegram **ausgeschaltet**.

1. Über [@BotFather](https://t.me/BotFather) einen eigenen Bot erstellen.
2. Den Bot als Administrator mit Veröffentlichungsrechten zum eigenen Kanal hinzufügen oder für einen privaten Chat den Bot zunächst starten.
3. In **Settings → Secrets and variables → Actions** des eigenen GitHub-Forks die Secrets `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` anlegen (Chat-ID oder `@kanalname`).
4. Telegram in `config.json` bzw. auf der Web-Konfigurationsseite aktivieren und speichern.

Nach der erfolgreichen Veröffentlichung unter GitHub Pages versendet der reguläre Produktionsworkflow optional das Video oder einen Link. Bei „Automatisch“ wird bei einem fehlgeschlagenen Video-Upload ein Link gesendet. Telegram-Fehler verhindern nicht die Website-Veröffentlichung. Videos über 49 MiB werden im Automatikmodus nur verlinkt. **Zugangsdaten niemals in `config.json` speichern.**

Hinweis: Die experimentelle parallele MuseTalk-Pipeline veröffentlicht noch nicht automatisch; Telegram hängt vorerst am regulären Produktionsworkflow. Der Versand ist noch nicht mit einem echten Telegram-Bot end-to-end getestet.

