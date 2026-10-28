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
