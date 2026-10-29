# Kurzupdates

`short-updates.html` zeigt die letzten **höchstens fünf** Kurzupdates. Jeder Eintrag läuft **24 Stunden nach Erstellung** ab. Die Seite blendet abgelaufene Einträge auch ohne erfolgreichen neuen Workflow aus. Beim nächsten Lauf werden die alten Einträge und ihre Audiodateien gelöscht.

Der Workflow `Create short news updates` prüft die konfigurierten Feeds viertelstündlich und kann manuell gestartet werden. GitHub kann geplante Ausführungen verzögern. Derselbe Veröffentlichungsschlüssel wie beim Sendungsworkflow verhindert gleichzeitige Schreibvorgänge. Die private Konfiguration wird aus `PERSONALNEWSHOST_CONFIG` geladen, falls vorhanden.

Neue Meldungen benötigen eine Veröffentlichungszeit innerhalb der letzten 60 Minuten, eine Beschreibung und ein Eil-/Entwicklungssignal im Titel. Atom-Änderungszeiten ersetzen keine fehlende Veröffentlichungszeit. Pro Lauf entsteht höchstens ein Update, zwischen Updates liegen mindestens 15 Minuten. Warnquellen benötigen weiterhin ihren eigenen Adapter.

Die Erstellung übernimmt Überschrift und vollständige Sätze der RSS-Beschreibung, mit Quelle und Veröffentlichungszeit. Kurze Texte erhalten eine Audiodatei über die bestehende lokale Sprachsynthese. Die Länge hängt vom Quelltext ab; 20–45 Sekunden sind kein garantiertes Format. Es gibt keine künstlich ergänzten Fakten. Längere Beschreibungen werden auf einen vollständigen Satz reduziert; bei weiterhin mehr als 110 Wörtern entfällt Audio.

Die Auswahl ist eine konservative Schlüsselwort-Heuristik, keine semantische Relevanzbewertung oder unabhängige Faktenprüfung. Ähnliche Titel werden zusammengehalten. Derselbe Artikel wird innerhalb des siebentägigen Erkennungsfensters auch nach einer Änderung nicht erneut veröffentlicht. Eine neue Entwicklung benötigt zunächst einen eigenen Artikel mit ausreichend abweichender Überschrift. Automatische Korrekturketten und ausdrückliche Verifikation durch mehrere Quellen sind noch nicht implementiert.

Optionen in `config.json` (Vorgaben gelten auch ohne diesen Block):

```json
"short_updates": {
  "enabled": true,
  "freshness_minutes": 60,
  "interval_minutes": 15
}
```

Die Grenzen von fünf Einträgen und 24 Stunden sind fest. `enabled: false` stoppt neue Einträge; vorhandene laufen weiter aus. Der öffentliche Status `short-update-state.json` enthält für sieben Tage Artikel-Hashes, Fingerprints und Zeiten zur Wiederholungserkennung, keine archivierten Meldungstexte. Änderungen am Workflow werden erst nach Übernahme auf den Standardbranch aktiv.

## Telegram

Nach erfolgreicher Veröffentlichung sendet der Kurzupdate-Workflow neue Kurzupdates als Text mit Zeit, Quelle und Link zur Kurzupdate-Seite an das vorhandene Telegram-Ziel (`telegram.target`). Voraussetzung sind `telegram.enabled` und die bestehenden Actions-Secrets `TELEGRAM_BOT_TOKEN` sowie `TELEGRAM_CHAT_ID` oder `TELEGRAM_CHAT_ID_SECONDARY`. Mit `short_updates.telegram_enabled: false` lässt sich nur der Kurzupdate-Versand abschalten; der Standard ist `true`.

Bereits versuchte Zustellungen werden pro Ziel und Update-ID sieben Tage in `.state/short-update-telegram.json` erkannt. Der Workflow schreibt diese Kennungen vor dem Netzwerkzugriff ins Repository; Bot-Token, Chat-ID und Meldungstexte stehen nicht im Zustellstatus. Nur Updates aus der letzten Stunde werden zugestellt. Bei Netzfehlern oder unklarer Bestätigung erfolgt kein automatischer Neuversand, um doppelte Meldungen zu verhindern. Das bedeutet: Ein Absturz nach der Reservierung kann eine Zustellung auslassen. Fehlgeschlagene Zustellungen machen den Actions-Lauf rot; die Website bleibt veröffentlicht. Zum gezielten Wiederholen muss die zugehörige Kennung bewusst aus dem Status entfernt werden.

Die Begrenzung auf fünf Einträge und 24 Stunden gilt auf der Website. Telegram-Nachrichten unterliegen weiterhin den Aufbewahrungseinstellungen des Zielchats; der Bot löscht sie nicht automatisch.

## Kurzupdate-Videos und Senderlogo

Kurzupdates mit verfügbarer Audiodatei erhalten ein MP4-Video mit Titel, Kurztext, Quelle und Zeit. Das gemeinsame Videologo `assets/logo-video.png` hat einen Alphakanal und ersetzt den bisherigen rechteckigen Hintergrund in neu erzeugten Sendungen und Kurzupdate-Videos. Alte Konfigurationen mit `assets/logo.png` werden auf die transparente Videoversion umgestellt, sofern diese vorhanden ist. Eigene Logo-Pfade und die Abschaltung durch einen leeren Pfad bleiben möglich.

Bei Kurzupdate-Videos steht oben rechts **AKTUELL** in Rot, links neben dem Senderlogo. Sendungen verwenden dasselbe Logo ohne diesen Zusatz. Die Playlist und die Kurzupdate-Seite spielen vorhandene Videos bevorzugt ab. Bei fehlendem Video bleiben Audio und Text verfügbar. Die Begrenzung auf fünf Kurzupdates und 24 Stunden gilt auch für die MP4-Dateien. Bestehende Audiodateien werden einmalig nachgerendert; Telegram veröffentlicht weiterhin den Kurztext mit Link zur Seite.
