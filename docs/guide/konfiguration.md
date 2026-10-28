# Konfiguration und Datenschutz

## Grundprinzip

PersonalNewsHost unterscheidet zwischen einer **öffentlichen Startkonfiguration** und einer **privaten Betriebskonfiguration**.

- `config.json` im Repository und `docs/config.json` auf GitHub Pages sind **öffentlich**. Sie dienen ausschließlich als Startwerte für die Weboberfläche und als Fallback, solange kein privates Secret eingerichtet ist.
- `PERSONALNEWSHOST_CONFIG` ist ein **GitHub Actions Secret** im jeweiligen Repository. Es enthält die beim Speichern über die Weboberfläche übertragene JSON-Konfiguration. Der Produktionsworkflow liest es zur Laufzeit und bevorzugt es gegenüber der öffentlichen Datei.
- GitHub Actions Secrets sind nach dem Speichern **nicht auslesbar** – auch nicht durch die Weboberfläche. Eine spätere Bearbeitung benötigt einen zuvor heruntergeladenen JSON-Export oder eine erneute Eingabe.
- `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` bleiben getrennte GitHub Actions Secrets. Tokens und Passwörter gehören **niemals** in die Konfigurationsdatei.

## Erste Einrichtung

1. Öffne die [Konfigurationsoberfläche](https://ploeffler.github.io/PersonalNewsHost/settings.html) bzw. die GitHub-Pages-Seite deines Forks.
2. Die Seite lädt die öffentliche `docs/config.json` als Startkonfiguration. Prüfe die RSS-Feeds und Einstellungen.
3. Lade über **Konfiguration herunterladen** eine lokale Sicherung herunter. Bewahre sie sicher auf, wenn du später dieselben Einstellungen bearbeiten möchtest.
4. Erstelle für dein Repository einen [Fine-grained GitHub Token](https://github.com/settings/personal-access-tokens/new) mit **Secrets: Read and write**. Für Bild-Uploads ist zusätzlich **Contents: Read and write** erforderlich.
5. Aktiviere die Speicherbestätigung und klicke **Direkt auf GitHub speichern**. Die Seite verschlüsselt die Konfiguration vor der Übertragung an die GitHub-API und speichert sie als `PERSONALNEWSHOST_CONFIG`.
6. Starte den Produktionsworkflow manuell. Er verwendet bei vorhandenem Secret die private Konfiguration; andernfalls die öffentliche Startkonfiguration.

**Wichtig:** Die Konfigurationsseite zeigt beim erneuten Öffnen nur die **öffentlichen Startwerte**, nicht die zuletzt im Secret gespeicherten Werte. Für Änderungen die eigene Sicherung importieren. Das Secret kann nur überschrieben, nicht zurückgelesen werden.

## Öffentliche Dateien und Forks

Ein Fork übernimmt die öffentlichen Dateien und ihre Git-Historie, **nicht** die GitHub Actions Secrets des Ursprungsprojekts. Die öffentliche `config.json` darf deshalb keine persönlichen Einstellungen oder Geheimnisse enthalten.

**Migrationshinweis:** In älteren Projektständen können `config.json` und `docs/config.json` noch individuelle Einstellungen enthalten. Vor dem Ersetzen durch neutrale Defaults die bisherige Konfiguration zuerst als `PERSONALNEWSHOST_CONFIG` speichern und lokal sichern. Andernfalls kann die laufende Produktion ihre Einstellungen verlieren.

Hochgeladene Bilder in `assets/` werden als Repository-Dateien veröffentlicht und sind **nicht privat**.

## Wichtige Einstellungen

| Feld | Funktion |
| --- | --- |
| `feeds` | HTTPS-Adressen der RSS-Quellen |
| `max_items` | Meldungen pro Sendung |
| `editorial.style` | Nachrichtenstil, standardmäßig `classic` |
| `media.mode` | Medienverwendung, standardmäßig `images_and_videos` |
| `presenter_settings` | Moderation, Portrait, Szenen und Lip-Sync-Optionen |
| `automation.enabled` | Automatische Produktion aktivieren oder deaktivieren |
| `automation.interval_hours` | Stundenraster |
| `automation.timezone` | IANA-Zeitzone, z. B. `Europe/Vienna` |
| `telegram.enabled` | Telegram-Versand aktivieren |

Der GitHub-Actions-Zeitplan prüft stündlich ungefähr um Minute 17 UTC, ob eine Produktion fällig ist. GitHub garantiert keine minutengenaue Ausführung. Verspätete oder ausgelassene Termine werden beim nächsten Lauf auf einem erlaubten Wochentag mit höchstens einer aktuellen Sendung nachgeholt; alte Sendungen werden nicht einzeln nachproduziert. Als Nachweis zählt das Veröffentlichungsdatum in `docs/feed.xml`, das erst nach erfolgreicher Produktion ins Repository übernommen wird. Fehlgeschlagene Versuche bleiben damit offen. Fehlt dieses Datum oder ist es unlesbar, erzeugt der nächste erlaubte Lauf eine Ausgabe. Bereits veröffentlichte Zeitfenster werden übersprungen. Nach dem Warten auf die gemeinsame Workflow-Sperre lädt der Produktionsworkflow den neuesten Branchstand, damit er auch zwischenzeitlich veröffentlichte Ausgaben berücksichtigt. Manuelle Starts sind unabhängig von der Automatik möglich.

## Sicherheit und Kosten

Die kostenlose CPU-Version ist für ein Budget von **0 € monatlichen Zusatzkosten** ausgelegt, unterliegt aber den GitHub-Freikontingenten und den Bedingungen externer Dienste. Die spätere GPU-Version mit kostenpflichtigen Diensten ist nicht automatisch aktiviert.

Verwende GitHub-Tokens nur auf einer vertrauenswürdigen Konfigurationsseite und niemals in Chats, Issues oder öffentlichen Dateien. Der Browser benötigt für das direkte Speichern einen Token; die Konfigurationsseite ist keine vollwertige Benutzerverwaltung.

## Senderlogo in der Sendung

Unter **Bilder → Senderlogo hochladen** lässt sich ein PNG- oder JPEG-Bild
(maximal 4 MB, mindestens 32×16 Pixel) hochladen. Ein transparentes PNG eignet
sich für einen Sender-Identifier ohne rechteckigen Hintergrund. Danach die
Konfiguration speichern, damit der eingetragene Bildpfad übernommen wird.

Das optionale Feld `station_logo` enthält den Repository-Pfad, beispielsweise
`assets/station-logo.png`. Das Bild erscheint während der gesamten Sendung
oben rechts mit 30 Pixel Abstand zum Rand und wird proportional auf maximal
160×90 Pixel skaliert. Ein leerer Pfad deaktiviert die Einblendung. Bestehende
Konfigurationen ohne dieses Feld verwenden standardmäßig `assets/logo.png`.

## Sendungsbereiche vorbereiten

Unter `editorial.broadcast_sections` sind Allgemein, Wirtschaft und Lokales
vorbereitet. `enabled: false` lässt Reihenfolge und Ansagen unverändert.
Die Bereichskennung wird bereits beim nächsten Lauf in `story-groups.json`
und `timeline.json` ausgegeben.

Mit `enabled: true` werden die ausgewählten Meldungen in der Reihenfolge von
`sections` gruppiert. Vor der ersten Meldung jedes belegten Bereichs wird
„Nun zum Bereich …“ gesprochen. Leere Bereiche werden ausgelassen.
Die bestehende Auswahl und die Gesamtzahl der Meldungen bleiben erhalten;
Bereiche haben noch keine eigenen Kontingente oder grafischen Trenner.

`feed_sections` ordnet vollständige Feed-URLs einer Bereichskennung zu und
hat Vorrang vor den Schlagwörtern in `sections[].keywords`. Schlagwörter
werden ohne Beachtung der Großschreibung als ganze Wörter im Titel gesucht.
Ohne Treffer greift `default` (Allgemein). Polizei Steiermark und der
Steiermark-Feed der Kleinen Zeitung sind Lokales zugeordnet. Dies ist eine
regelbasierte Vorbereitung; die Zuordnung sollte redaktionell geprüft werden.
