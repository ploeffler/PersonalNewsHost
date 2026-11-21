# Feed-Fehler: Wiederholung, Ersatzkopie und Benachrichtigung

Fällt ein einzelner RSS-Feed aus, läuft die Sendung mit den übrigen Feeds weiter. `scripts/feed_resilience.py` wird von `scripts/generate.py` (Sendung und Kurzupdates) und `scripts/collect_news.py` (Nachrichtenspeicher) für jeden Feed-Abruf verwendet.

## Ablauf pro Feed

1. **Abruf mit Zeitlimit** (12 Sekunden je Versuch).
2. **Wiederholung mit wachsenden Pausen**, nur bei vorübergehenden Fehlern: Zeitüberschreitung, Verbindungsfehler, HTTP 5xx und 429. Standard: 3 Versuche, Pausen 2 und 6 Sekunden. Ungültige Adressen, HTTP 4xx und kaputtes XML werden nicht wiederholt.
3. **Ersatzkopie:** Jeder erfolgreich gelesene Feed wird als letzte gültige Kopie gespeichert. Scheitert ein Feed endgültig oder liefert er kaputtes XML, wird die Kopie verwendet, solange sie höchstens `cache_max_age_hours` alt ist (Standard 48 h). Eine kaputte Antwort ersetzt die gute Kopie nie.
4. **Ohne brauchbare Kopie** wird der Feed in diesem Lauf übersprungen. Erst wenn kein einziger Feed Einträge liefert, bricht die Sendung ab; die zuletzt veröffentlichte Ausgabe bleibt dann bestehen.

## Ablage

Ersatzkopien und Zustand liegen in `.cache/feeds/` (in `.gitignore`). Die Workflows `news.yml` und `short-updates.yml` übertragen den Ordner mit `actions/cache` von Lauf zu Lauf. Feed-Inhalte Dritter gelangen so nicht ins öffentliche Repository. Der Zustand (`health.json`) verwendet Hash-Schlüssel statt Feed-Adressen.

Ein Workflow-Lauf zählt als ein Fehlversuch, auch wenn mehrere Skripte denselben Feed lesen (Abrufe innerhalb von 5 Minuten werden zusammengefasst). Ein erfolgreicher Abruf setzt den Zähler zurück.

## Benachrichtigung

Der Workflow-Schritt `python3 scripts/feed_resilience.py --notify` meldet Feeds, die `failure_threshold` Läufe in Folge gescheitert sind (Standard 3), höchstens einmal je Feed und `notify_interval_hours` (Standard 24 h):

- **Telegram an einen Admin-Chat**, wenn die Secrets `TELEGRAM_BOT_TOKEN` und `TELEGRAM_ADMIN_CHAT_ID` gesetzt sind. Die Nachricht nennt Feed-Nummer und Host, Zahl der Fehlversuche, Dauer und Fehlerart.
- **GitHub-Issue** (Opt-in über `notify.github_issue: true`). Das Issue ist öffentlich und nennt daher nur die Position des Feeds in der Konfiguration und die Fehlerart, nie Adresse oder Host. Die Workflows haben dafür `issues: write`.

Ohne gesetzte Secrets wird nichts gesendet; der Lauf schreibt nur einen Hinweis ins Log und versucht es beim nächsten Lauf erneut. Ein Fehler beim Senden lässt den Workflow nicht scheitern.

## Konfiguration

```json
"feed_resilience": {
  "attempts": 3,
  "backoff_seconds": [2, 6],
  "cache_max_age_hours": 48,
  "failure_threshold": 3,
  "notify_interval_hours": 24,
  "notify": {"telegram": true, "github_issue": false}
}
```

Werte außerhalb der erlaubten Bereiche werden begrenzt (z. B. höchstens 5 Versuche, Pausen höchstens 60 Sekunden). `cache_max_age_hours: 0` schaltet die Ersatzkopie praktisch ab.
