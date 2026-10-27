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
