# Nachrichtenübersicht auf der Hauptseite

Unter dem Player stehen alle gespeicherten Meldungen innerhalb der letzten 24 Stunden, neueste zuerst. Überschriften sind groß, darunter steht der gespeicherte RSS-Nachrichtentext kleiner. Fehlt der Veröffentlichungstermin, wird die erstmalige Erfassung verwendet und ausdrücklich als „Erfasst“ angezeigt. Artikelaktualisierungen setzen das Alter nicht zurück.

Die ausgewählten Beiträge der letzten langen Sendung tragen „Letzte Sendung · Beitrag …“. Meldungen aus Kurzupdates seit dieser Sendung tragen eine rote Kennzeichnung. Diese Zuordnung bleibt unabhängig vom abgespielten Playlist-Eintrag. Eine Meldung kann beide Kennzeichnungen tragen. Meldungen außerhalb der 24-Stunden-Grenze werden auch dann ausgeblendet, wenn sie zur letzten Sendung gehören.

Darunter steht die RSS-Quellenliste mit den Bezeichnungen der konfigurierten Feeds. Die Bezeichnungen stammen aus den RSS-/Atom-Kanaltiteln; die Links führen zu den Feeds.

`collect_news.py` liest alle Einträge der konfigurierten Feeds, ohne die Begrenzung der Videoauswahl. Die Sendungs- und Kurzupdate-Workflows aktualisieren `docs/news-store.json`. Bereits erfasste Meldungen bleiben innerhalb des Zeitfensters erhalten, auch wenn ein Feed sie nicht mehr liefert oder vorübergehend ausfällt. Der erste Lauf kann nur aktuell angebotene Feed-Einträge und gespeicherte Sendungs-/Kurzupdate-Texte übernehmen. Erkennungsmetadaten ohne Nachrichtentext verhindern, dass undatierte oder nur aktualisierte Einträge künstlich erneut aktuell werden.

Die Seite prüft Änderungen jede Minute und den Ablauf alle 30 Sekunden. Die Obergrenze von fünf Kurzupdate-Videos begrenzt nicht den Nachrichtenspeicher. Kennzeichnungen bereits erfasster Kurzupdate-Meldungen bleiben bis zum Ablauf der Meldung erhalten.
