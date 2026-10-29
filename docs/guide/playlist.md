# Playlist auf der Hauptseite

Die Hauptseite zeigt rechts neben dem Player eine Playlist mit den neuesten Beiträgen zuerst:

1. Noch vorhandene Kurzupdates seit der neuesten Sendung, neueste zuerst.
2. Neueste Sendung.
3. Noch vorhandene Kurzupdates zwischen den beiden Sendungen, neueste zuerst.
4. Vorletzte Sendung.

Beim Öffnen ist die neueste Sendung ausgewählt. Ein Klick wechselt den Player und die Quellen. Für Sendungen gehören auch Transkript und Untertitel zur ausgewählten Ausgabe. Kurzupdates verwenden ihre vorhandene Audiodatei; reine Textupdates zeigen den Text im Playerbereich. Die Kennzeichnung VIDEO, AUDIO oder TEXT macht das Format sichtbar. Auf kleinen Bildschirmen steht die Playlist unter dem Player.

Der Generator legt die letzten zwei erfolgreich produzierten Sendungen samt Transkript und Untertiteln im Verzeichnis `docs/broadcasts/` ab. `docs/broadcasts.json` enthält die Metadaten und Quellen. Bei einer neuen Sendung wird die älteste dieser Archivkopien entfernt. `latest.mp4` und die bisherigen RSS-Adressen bleiben erreichbar. Die ersten beiden Einträge wurden aus den vorhandenen Sendungsständen der Git-Historie übernommen.

Kurzupdates kommen weiterhin aus `short-updates.json`: maximal fünf Einträge, höchstens 24 Stunden alt. Ältere Kurzupdates werden für die Playlist nicht wiederhergestellt. Die Seite prüft neue Daten jede Minute und blendet abgelaufene Updates auch bei länger geöffnetem Browser aus. Bei fehlenden Playlist-Daten bleibt das bisherige aktuelle Video nutzbar.

Die Dateien `playlist.css` und `playlist.js` liegen lokal auf der Seite. Die Gestaltung wird bei jeder Sendungsproduktion über `scripts/broadcast_archive.py` in die neue Hauptseite eingefügt.
