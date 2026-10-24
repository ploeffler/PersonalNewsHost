# PersonalNewsHost – Schritt-für-Schritt-Installation

Diese Anleitung richtet sich an Personen, die das öffentliche Projekt in ihrem **eigenen GitHub-Fork** betreiben möchten. Ein eigener Server und ein dauerhaft geöffneter Browser sind nicht nötig. Die kostenlosen GitHub-Kontingente und Nutzungsbedingungen gelten weiterhin.

## 1. Voraussetzungen

Du benötigst ein GitHub-Konto und einen Browser. Optional benötigst du einen Telegram-Account für die Bot-Einrichtung. Für die ersten Schritte ist kein Telegram-Bot erforderlich.

## 2. Repository forken

1. Öffne [PersonalNewsHost](https://github.com/ploeffler/PersonalNewsHost).
2. Klicke rechts oben auf **Fork** und erstelle eine Kopie in deinem GitHub-Konto.
3. Arbeite ab jetzt ausschließlich in **deinem Fork**. GitHub übernimmt beim Forken **keine Actions Secrets** des Originalprojekts.

## 3. GitHub Actions aktivieren

1. Öffne in deinem Fork den Reiter **Actions**.
2. Falls GitHub einen Hinweis anzeigt, aktiviere Workflows für den Fork.
3. Automatische Produktionsläufe sind in den Defaultwerten ausgeschaltet. Ein manueller Test ist später möglich.

## 4. GitHub Pages einrichten

1. Öffne **Settings → Pages** in deinem Fork.
2. Wähle **Deploy from a branch**, Branch **main**, Ordner **/docs** und speichere.
3. Die öffentliche Adresse lautet typischerweise `https://DEIN-NAME.github.io/PersonalNewsHost/`. Die Bereitstellung kann einige Minuten dauern.

## 5. Weboberfläche öffnen

1. Öffne die Pages-Adresse deines Forks und dort die **Konfiguration** (`settings.html`).
2. Beim ersten Aufruf werden die öffentlichen Defaultwerte aus `docs/config.json` geladen.
3. Passe RSS-Feeds, Moderator, Sprache, Ausgabe und Automatik an. Verwende nur RSS-Quellen und Medien, deren Nutzung erlaubt ist.

## 6. Persönliche Konfiguration sicher speichern

Die Weboberfläche kann die Einstellungen verschlüsselt im **GitHub Actions Secret `PERSONALNEWSHOST_CONFIG` deines Forks** ablegen. Dafür benötigt sie einen Fine-grained GitHub Personal Access Token mit **Secrets: Read and write** für genau deinen Fork. Für den manuellen Produktionsstart ist zusätzlich **Actions: Read and write** erforderlich; Bild-Uploads benötigen **Contents: Read and write**.

1. Erstelle den Fine-grained Token in deinen GitHub-Kontoeinstellungen. Wähle als Repository ausschließlich deinen Fork.
2. Gib den Token auf der Konfigurationsseite ein.
3. Bestätige den Speichervorgang und klicke auf **Direkt auf GitHub speichern**.
4. Prüfe unter **Settings → Secrets and variables → Actions**, dass `PERSONALNEWSHOST_CONFIG` vorhanden ist.
5. Bewahre zusätzlich eine **lokale Kopie** deiner Einstellungen an einem geschützten Ort auf: GitHub erlaubt nicht, den Wert eines Secrets nachträglich wieder auszulesen.

**Wichtig:** Die Weboberfläche ist eine statische Webseite. Das Verschlüsseln im Browser und Speichern über die GitHub-API muss noch mit einem echten Token end-to-end geprüft werden. Teile den Token nicht und verwende die Seite nur unter einer vertrauenswürdigen Adresse. `config.json` im Repository bleibt öffentlich und darf keine Geheimnisse enthalten.

## 7. Erste Nachrichtensendung erzeugen

1. Öffne **Actions → Generate news video** in deinem Fork.
2. Wähle **Run workflow** auf Branch **main**.
3. Warte, bis der Lauf abgeschlossen ist; prüfe bei Fehlern die Job-Logs.
4. Öffne die GitHub-Pages-Seite deines Forks. Die aktuelle Sendung steht dort als `latest.mp4` bereit; der Video-RSS-Feed als `feed.xml`.

## 8. Automatische Produktion aktivieren

Stelle auf der Konfigurationsseite die gewünschte Automatik ein und speichere erneut als Secret. Der GitHub-Actions-Zeitplan prüft regelmäßig, ob ein Lauf fällig ist. GitHub garantiert keine minutengenaue Ausführung.

## 9. Optional: Telegram einrichten

1. Erstelle mit [@BotFather](https://t.me/BotFather) einen **eigenen Bot**.
2. Erstelle einen Kanal oder starte einen privaten Chat mit dem Bot. Erteile im Kanal nur die nötigen Rechte zum Senden und Löschen.
3. Speichere im **eigenen Fork** unter **Settings → Secrets and variables → Actions** die Secrets `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID`.
4. Aktiviere Telegram in der Webkonfiguration und speichere die Einstellungen.
5. Starte einen Testlauf und prüfe den tatsächlichen Versand.

Die Telegram-Nachrichten werden durch einen separaten Workflow **frühestens nach 25 Stunden** gelöscht, soweit GitHub Actions rechtzeitig ausgeführt wird und Telegram die Löschung noch erlaubt. Das MP4 auf GitHub Pages bleibt davon unberührt. Telegram ist standardmäßig deaktiviert.

## 10. Fehlerbehebung und Sicherheit

- **Keine Sendung:** Prüfe, ob der Workflow erfolgreich war, RSS-Feeds erreichbar sind und die Konfiguration gültig ist.
- **Secret fehlt:** Prüfe den Namen `PERSONALNEWSHOST_CONFIG` im **eigenen** Repository.
- **Speichern schlägt fehl:** Prüfe die Berechtigungen und Repository-Auswahl des Fine-grained Tokens.
- **Telegram sendet nicht:** Prüfe Bot-Token, Chat-ID, Bot-Rechte und Workflow-Logs.
- **Fork-Sicherheit:** Forks erhalten weder die Secrets des Originals noch Zugriff darauf. Öffentliche Konfigurationsdateien werden hingegen mitkopiert.
- **Geheimnisse niemals committen:** Auch nach einem Löschen können sie in der Git-Historie verbleiben.

Weiterführende Dokumentation: [Konfiguration](konfiguration.md) · [Betrieb und Sicherheit](betrieb-und-sicherheit.md) · [Technik](technik.md).
