# betrieb und sicherheit

## Funktionsstand

| Funktion | Status |
| --- | --- |
| Konfigurierbare RSS-Quellen | Produktiv |
| Regelbasierte Auswahl von Meldungen | Produktiv |
| Deutsche Sprachausgabe mit Piper `de_DE-thorsten-high` | Produktiv |
| eSpeak-NG als Fallback bei fehlendem Piper-Modell | Produktiv |
| MP4, Webseite, Transkript und Video-RSS | Produktiv |
| GitHub-Zeitplan (Rückfallebene) | Aktiv um 7:05, 12:05 und 20:05 Uhr (Europe/Vienna), best effort; regulärer Takt über externen Taktgeber (siehe unten) |
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


## Zuverlässiger Zeitplan mit externem Taktgeber (optional)

GitHub startet Zeitplan-Läufe (`schedule`) nur nach Möglichkeit. Bei hoher Last werden viele Auslöser verzögert oder ganz ausgelassen. Im November 2026 lief der stündliche Sendungsworkflow so nur drei- bis fünfmal am Tag, der viertelstündliche Kurzupdate-Workflow teilweise nur viermal am Tag. Abhilfe schafft ein kostenloser externer Cron-Dienst, zum Beispiel [cron-job.org](https://cron-job.org), der die Workflows über die GitHub-API startet. Der GitHub-Zeitplan bleibt als Rückfallebene aktiv und startet beide Workflows zusätzlich um 7:05, 12:05 und 20:05 Uhr (Europe/Vienna). Fällt der externe Dienst aus, erscheinen so weiterhin bis zu drei Sendungen am Tag.

**Doppelte Sendungen entstehen dabei nicht:** Der externe Taktgeber startet die Sendung mit `trigger=schedule`. Dann prüft `scripts/check_schedule.py` wie beim GitHub-Zeitplan, ob ein Zeitfenster fällig und noch nicht veröffentlicht ist. Ein manueller Start in der Actions-Oberfläche (Standard `trigger=manual`) produziert weiterhin immer. Kurzupdates erkennen bereits veröffentlichte Meldungen selbst; zusätzliche Läufe erzeugen keine Duplikate.

### 1. Eingeschränkten GitHub-Token anlegen

1. Auf GitHub **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token** öffnen.
2. **Repository access:** *Only select repositories* und ausschließlich das eigene PersonalNewsHost-Repository wählen.
3. **Permissions → Repository permissions → Actions:** *Read and write*. Alle anderen Rechte bleiben auf *No access* (Metadata ist automatisch lesend).
4. Ablaufdatum setzen (z. B. 1 Jahr) und sich daran erinnern, den Token rechtzeitig zu erneuern.

Dieser Token kann nur Workflows starten, abbrechen oder Läufe verwalten. Er kann keinen Code ändern und keine Secrets lesen. Trotzdem gilt: nur beim Cron-Dienst hinterlegen, nie in das Repository, `config.json`, Issues oder Screenshots. Bei Verdacht auf Offenlegung auf GitHub widerrufen.

### 2. Zwei Cron-Jobs anlegen

Für beide Jobs gilt: Methode **POST**, Zeitzone beliebig, und diese HTTP-Header:

```
Accept: application/vnd.github+json
Authorization: Bearer <TOKEN>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

| Job | URL | Body | Zeitplan |
| --- | --- | --- | --- |
| Sendung | `https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/news.yml/dispatches` | `{"ref":"main","inputs":{"trigger":"schedule"}}` | stündlich, Minute 17 |
| Kurzupdates | `https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/short-updates.yml/dispatches` | `{"ref":"main"}` | Minute 7, 22, 37 und 52 |

`<OWNER>/<REPO>` durch das eigene Repository ersetzen, z. B. `ploeffler/PersonalNewsHost`. GitHub antwortet bei Erfolg mit **HTTP 204** (ohne Inhalt). Den Job im Cron-Dienst so einstellen, dass er bei Fehlern benachrichtigt. Test von der Kommandozeile:

```
curl -X POST -H "Accept: application/vnd.github+json" -H "Authorization: Bearer <TOKEN>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/news.yml/dispatches \
  -d '{"ref":"main","inputs":{"trigger":"schedule"}}'
```

Im Log des Schritts „Check configured production schedule“ steht danach `Production enabled …` oder `Production skipped …: latest due slot already published`.

### Grenzen

- Beide Workflows teilen sich die Sperre `personalnewshost-publish`. GitHub hält je Sperre nur einen wartenden Lauf; kommt ein weiterer hinzu, wird der ältere wartende abgebrochen. Die versetzten Minuten (Sendung :17, Kurzupdates :07/:22/:37/:52) halten Überschneidungen gering. Eine ausgefallene Sendung holt der nächste Lauf nach.
- Zusätzliche Läufe verbrauchen Actions-Minuten. Für öffentliche Repositories sind Standard-Runner kostenlos; private Forks verbrauchen ihr Freikontingent. Der Prüfschritt einer nicht fälligen Sendung dauert nur wenige Sekunden.
- Der externe Dienst ist ein weiterer Anbieter mit eigenen Nutzungsbedingungen und Verfügbarkeit.


## Telegram für eigene Forks (optional)

**Sicherheit bei Forks:** GitHub kopiert beim Forken **keine Repository- oder Actions-Secrets**. Ein Fork kann deshalb weder den Bot-Token noch die Chat-ID des ursprünglichen PersonalNewsHost-Repositories lesen oder verwenden. `${{ secrets.TELEGRAM_BOT_TOKEN }}` und `${{ secrets.TELEGRAM_CHAT_ID }}` beziehen sich immer auf die Secrets des Repositories, in dem der Workflow läuft. Ohne eigene Secrets ist der Telegram-Versand nicht möglich; bei aktivierter Telegram-Option meldet der Versand einen Fehler, ohne die Website-Veröffentlichung rückgängig zu machen. Jeder Fork-Betreiber benötigt einen **eigenen Bot-Token und ein eigenes Ziel**. Es gibt keine gemeinsamen oder fest im Quellcode hinterlegten Telegram-Zugangsdaten.

**Schutz des Originalprojekts:** Tokens niemals in `config.json`, Workflow-Dateien, Commits, Issues, Pull Requests, Screenshots oder Logs eintragen. Ausschließlich **Settings → Secrets and variables → Actions** verwenden. GitHub-Secrets werden zwar in Logs nach Möglichkeit maskiert, aber die Maskierung ist keine vollständige Sicherheitsgrenze. Wer Schreibzugriff auf Workflows im Originalrepository hat, kann potenziell dessen Secrets missbrauchen; deshalb Schreibrechte und Workflow-Änderungen streng begrenzen. Bei Verdacht auf Offenlegung den Token über BotFather widerrufen und ersetzen.

**Telegram-Ablaufzeit:** Die Aufbewahrung und Löschung werden direkt im Telegram-Ziel eingestellt. PersonalNewsHost löscht keine Nachrichten.

Jeder Fork kann Telegram unabhängig aktivieren. In der Web-Konfiguration unter „Telegram-Veröffentlichung“ sind Empfängerart (Kanal, privater Chat, Gruppe) und Versandart (automatisch, nur Video, nur Link) wählbar. Standardmäßig ist Telegram **ausgeschaltet**.

1. Über [@BotFather](https://t.me/BotFather) einen eigenen Bot erstellen.
2. Den Bot als Administrator mit Veröffentlichungsrechten zum eigenen Kanal hinzufügen oder für einen privaten Chat den Bot zunächst starten.
3. In **Settings → Secrets and variables → Actions** des eigenen GitHub-Forks die Secrets `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` anlegen (Chat-ID oder `@kanalname`).
4. Telegram in `config.json` bzw. auf der Web-Konfigurationsseite aktivieren und speichern.

Nach der erfolgreichen Veröffentlichung unter GitHub Pages versendet der reguläre Produktionsworkflow optional das Video oder einen Link. Bei „Automatisch“ wird bei einem fehlgeschlagenen Video-Upload ein Link gesendet. Telegram-Fehler verhindern nicht die Website-Veröffentlichung. Videos über 49 MiB werden im Automatikmodus nur verlinkt. **Zugangsdaten niemals in `config.json` speichern.**

Hinweis: Die experimentelle parallele MuseTalk-Pipeline veröffentlicht noch nicht automatisch; Telegram hängt vorerst am regulären Produktionsworkflow. Der Versand ist noch nicht mit einem echten Telegram-Bot end-to-end getestet.



### Zielwahl und optionale Löschung

In den Telegram-Einstellungen steht jetzt „Zielkanal“ zur Verfügung:
`default` verwendet das Actions-Secret `TELEGRAM_CHAT_ID`, `secondary` das
Secret `TELEGRAM_CHAT_ID_SECONDARY`. Beide Ziele verwenden denselben Bot aus
`TELEGRAM_BOT_TOKEN`. Bot-Token und Chat-IDs niemals in JSON oder HTML eintragen.
Der Bot benötigt im jeweiligen Kanal die Berechtigung zum Veröffentlichen
seiner Nachrichten. Die vorhandene Empfängerart ist nur eine Beschreibung.

Die Löschfrist wird direkt im Telegram-Ziel definiert. PersonalNewsHost plant
keine Löschungen und ruft keine Telegram-Löschfunktion auf. Der bisherige
Cleanup-Workflow wurde entfernt; der alte Skript-Einstieg bleibt ohne Löschwirkung.
Bereits vorhandene Löschlisten bleiben unverändert und werden nicht ausgeführt.
Das alte Konfigurationsfeld `telegram.auto_delete` wird ignoriert.

Der Produktionsworkflow entfernt das alte Video vor der Generierung und prüft
anschließend mit ffprobe auf eine Videospur. Erst nach erfolgreicher Generierung
und Git-Veröffentlichung folgt der optionale Versand. Bei unklarem Upload-Ergebnis
(z. B. Timeout) erfolgt kein automatischer Link-Nachversand, um Doppelposts zu vermeiden.
Ein manueller Start des Produktionsworkflows kann bei aktiviertem Telegram senden.

Es werden keine kostenpflichtigen Dienste oder zusätzlichen Pakete benötigt.
Standard-Ubuntu-Runner sind für öffentliche Repositories kostenlos; bei privaten
Forks gelten die GitHub-Freikontingente. Quellen:
[GitHub Actions Abrechnung](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[Telegram deleteMessage](https://core.telegram.org/bots/api#deletemessage).

Offline-Prüfung: `python3 -m unittest discover -s tests -p test_telegram.py -v`.
Diese Tests ersetzen alle Telegram-Netzwerkaufrufe durch Mocks.
Ein echter Versandtest erfordert eine ausdrückliche Freigabe.
