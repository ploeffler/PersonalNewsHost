# Kurzupdates

`short-updates.html` zeigt die letzten **höchstens fünf** Kurzupdates. Jeder Eintrag läuft **24 Stunden nach Erstellung** ab. Die Seite blendet abgelaufene Einträge auch ohne erfolgreichen neuen Workflow aus. Beim nächsten Lauf werden die alten Einträge und ihre Audiodateien gelöscht.

Der Workflow `Create short news updates` prüft die konfigurierten Feeds viertelstündlich und kann manuell gestartet werden. GitHub kann geplante Ausführungen verzögern oder auslassen; ein [externer Taktgeber](betrieb-und-sicherheit.md#zuverlässiger-zeitplan-mit-externem-taktgeber-optional) macht den Takt zuverlässiger. Derselbe Veröffentlichungsschlüssel wie beim Sendungsworkflow verhindert gleichzeitige Schreibvorgänge. Die private Konfiguration wird aus `PERSONALNEWSHOST_CONFIG` geladen, falls vorhanden.

Kurzupdates sind für **Eilmeldungen** gedacht. Der viertelstündliche RSS-Lauf speichert zuerst alle Feed-Meldungen im Nachrichtenspeicher und entscheidet danach, ob ein Kurzupdate nötig ist. Bewertet werden nicht einzelne Meldungen, sondern **Ereignisse** – Gruppen von Meldungen verschiedener Medien über dasselbe Geschehen aus der [redaktionellen Pipeline](redaktionelle-pipeline.md). Ein Ereignis ist eine Eilmeldung, wenn eine dieser Bedingungen gilt:

1. **Kennzeichnung:** Eine Überschrift enthält „Eilmeldung“, „Eil“, „Breaking“ oder „+++“, oder die Meldung stammt aus einem in `breaking_feeds` eingetragenen Eil-Feed. Ein Medium genügt.
2. **Schwere:** Tote, Explosion, Anschlag, Einsturz, Schüsse, Erdbeben, Evakuierung, Geiselnahme, Absturz, Krieg u. Ä. – und mindestens `min_publishers` (Standard 2) verschiedene Medien berichten innerhalb von `window_minutes` (Standard 180). „Tote“ zählt nur als Hauptwort; Meldungen über Tiere (z. B. „400 tote Schweine“) zählen nicht.
3. **Spitzenamt:** Rücktritt, Entlassung, Festnahme oder Tod in einem hohen Amt (Kanzler, Präsident, Minister, Regierung, Konzernchef, Papst, Landeshauptmann …), ebenfalls von mindestens zwei Medien.
4. **Österreich-Bezug:** Das Ereignis betrifft Österreich (Land, Bundesländer, größere Städte, Bundesregierung, Parteien, ÖBB, Asfinag …) **und** ist dringlich (Drohung, Warnung, Alarm, Neuwahl, Regierungskrise, Ausweisung, Unwetter, Hochwasser, Lawine, Stromausfall, Streik, Großeinsatz, Vermisste, Razzia …), ebenfalls von mindestens zwei Medien. Abschaltbar mit `austria_rule: false`.

Zusätzlich gilt: Die neueste Meldung des Ereignisses ist höchstens `freshness_minutes` (Standard 60) alt, und das Ereignis begann vor höchstens `window_minutes`. Pro Lauf entsteht höchstens ein Kurzupdate, zwischen zwei Kurzupdates liegen mindestens `interval_minutes` (Standard 15), pro Kalendertag (Europe/Vienna) höchstens `max_per_day` (Standard 6). Zu einem bereits gemeldeten Ereignis entsteht drei Tage lang kein weiteres Kurzupdate.

Bei einer Prüfung mit den gespeicherten Meldungen vom 7. bis 13.11.2026 hätte die alte Schlagwortregel 37 Kurzupdates erzeugt, darunter viele Sportergebnisse und Sperren; die neue Regel 15, fast ausschließlich echte Eilmeldungen.

Der Text ist der geprüfte, wörtliche Mehrquellen-Text der redaktionellen Pipeline (Überschrift, Sätze aus den Quellen, „Quellen: …“). Es werden keine Fakten ergänzt. Bei mehr als 110 Wörtern wird auf Überschrift, einen Satz und die Quellenangabe gekürzt.

**Laufzeit:** Sprachsynthese und Videowerkzeuge werden nur installiert, wenn ein neues Kurzupdate Ton oder Video braucht. Ein Lauf ohne Eilmeldung kommt ohne sie aus. Scheitert die Medienerzeugung, wird sie höchstens zweimal versucht; Text und Link bleiben verfügbar.

Die Erkennung ist eine regelbasierte Heuristik ohne KI, keine unabhängige Faktenprüfung. Widersprüchliche Zahlen zwischen den Quellen stellen ein Ereignis wie in der Sendung zurück.

Optionen in `config.json` (Vorgaben gelten auch ohne diesen Block):

```json
"short_updates": {
  "enabled": true,
  "freshness_minutes": 60,
  "window_minutes": 180,
  "min_publishers": 2,
  "max_per_day": 6,
  "interval_minutes": 15,
  "austria_rule": true,
  "breaking_feeds": [],
  "timezone": "Europe/Vienna"
}
```

Die Grenzen von fünf Einträgen und 24 Stunden sind fest. `enabled: false` stoppt neue Einträge; vorhandene laufen weiter aus. Der öffentliche Status `short-update-state.json` enthält die Kurzupdates und für drei Tage die Artikel-Kennungen bereits gemeldeter Ereignisse. Änderungen am Workflow werden erst nach Übernahme auf den Standardbranch aktiv.

## Telegram

Nach erfolgreicher Veröffentlichung sendet der Kurzupdate-Workflow neue Kurzupdates als Text mit Zeit, Quelle und Link zur Kurzupdate-Seite an das vorhandene Telegram-Ziel (`telegram.target`). Voraussetzung sind `telegram.enabled` und die bestehenden Actions-Secrets `TELEGRAM_BOT_TOKEN` sowie `TELEGRAM_CHAT_ID` oder `TELEGRAM_CHAT_ID_SECONDARY`. Mit `short_updates.telegram_enabled: false` lässt sich nur der Kurzupdate-Versand abschalten; der Standard ist `true`.

Bereits versuchte Zustellungen werden pro Ziel und Update-ID sieben Tage in `.state/short-update-telegram.json` erkannt. Der Workflow schreibt diese Kennungen vor dem Netzwerkzugriff ins Repository; Bot-Token, Chat-ID und Meldungstexte stehen nicht im Zustellstatus. Nur Updates aus der letzten Stunde werden zugestellt. Bei Netzfehlern oder unklarer Bestätigung erfolgt kein automatischer Neuversand, um doppelte Meldungen zu verhindern. Das bedeutet: Ein Absturz nach der Reservierung kann eine Zustellung auslassen. Fehlgeschlagene Zustellungen machen den Actions-Lauf rot; die Website bleibt veröffentlicht. Zum gezielten Wiederholen muss die zugehörige Kennung bewusst aus dem Status entfernt werden.

Die Begrenzung auf fünf Einträge und 24 Stunden gilt auf der Website. Telegram-Nachrichten unterliegen weiterhin den Aufbewahrungseinstellungen des Zielchats; der Bot löscht sie nicht automatisch.

## Kurzupdate-Videos und Senderlogo

Kurzupdates mit verfügbarer Audiodatei erhalten ein MP4-Video mit Titel, Kurztext, Quelle und Zeit. Das gemeinsame Videologo `assets/logo-video.png` hat einen Alphakanal und ersetzt den bisherigen rechteckigen Hintergrund in neu erzeugten Sendungen und Kurzupdate-Videos. Alte Konfigurationen mit `assets/logo.png` werden auf die transparente Videoversion umgestellt, sofern diese vorhanden ist. Eigene Logo-Pfade und die Abschaltung durch einen leeren Pfad bleiben möglich.

Bei Kurzupdate-Videos steht oben rechts **AKTUELL** in Rot, links neben dem Senderlogo. Sendungen verwenden dasselbe Logo ohne diesen Zusatz. Die Playlist und die Kurzupdate-Seite spielen vorhandene Videos bevorzugt ab. Bei fehlendem Video bleiben Audio und Text verfügbar. Die Begrenzung auf fünf Kurzupdates und 24 Stunden gilt auch für die MP4-Dateien. Bestehende Audiodateien werden einmalig nachgerendert; Telegram veröffentlicht weiterhin den Kurztext mit Link zur Seite.
