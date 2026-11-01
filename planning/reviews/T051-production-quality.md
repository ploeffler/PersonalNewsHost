# T051: Qualitätsgrenze vor Übernahme einer Ausgabe

Der Generator arbeitet jetzt in einem temporären Geschwisterverzeichnis. Statische
Dateien und bisheriges Archiv werden übernommen; alte aktuelle Videodatei und
Prüfmetadaten werden aus dem Kandidaten entfernt. Ein alter Erfolg kann damit
keinen fehlgeschlagenen neuen Lauf maskieren. Nach Rendering werden Meldungszahl,
Titel/Quellen, durchgehende nichtleere Abschnitte, Timeline, Videodauer, Video- und
Tonspur sowie Transkript geprüft. Erst danach erfolgt der Verzeichnistausch.

Eine Quelle muss eine HTTP(S)-URL haben. Die Prüfung bestätigt keine sachliche
Richtigkeit oder Erreichbarkeit. Standard: mindestens eine Meldung, mindestens
0,1 Sekunden, maximal konfigurierte target_duration_seconds oder Timeline + 1 s.
Abweichung von der Audio-Timeline maximal 1 s bzw. 2 %. Optionales quality-Objekt
in der Basiskonfiguration unterstützt min_items, min_duration_seconds und
max_duration_seconds; alle Grenzen müssen den gerenderten Kandidaten erfüllen.
Die Dauer wird per ffprobe ermittelt, nicht aus einem erfolgreichen Exitcode geraten.

Bei Render-/Qualitätsfehlern bleiben letzte Video-, Feed-, Seiten- und Begleitdateien
erhalten. Nur ein neuer redaktioneller Diagnosebericht wird bewusst übernommen,
auch wenn keine Meldung freigegeben wurde. Bei fehlgeschlagenem finalem Rename
wird das vorherige Ausgabeverzeichnis zurückgestellt. Temporäre Daten werden
aufgeräumt. Erfolgsmetadaten stehen in production-quality.json.

Sechs gezielte Tests decken gültige/ungültige Medienverträge, Erhalt der alten
Ausgabe, Übernahme mit statischen Assets, fehlgeschlagenen Rename und Ausschluss
alter Medien aus der Kandidatenprüfung ab. Bestehender realer Offline-Feed-/Video-
Test bestanden. Gesamtergebnis im Aufgabenreview.

Grenzen: ein aktiver Producer pro Ausgabeordner; prozessübergreifende Sperren und
Wiederaufnahme nach hartem Prozess-/Hostabbruch folgen im Betriebsunterbau.
Der zweistufige Verzeichnistausch schützt behandelte Fehler, ist aber keine
Datenbanktransaktion über Stromausfälle. Es gibt kurzzeitig keinen Pfad zwischen
den beiden Renames. Kopie bisheriger statischer/Archivdaten benötigt temporär
zusätzlichen Speicher. Symlinks im Ausgabeordner werden vor Verarbeitung verweigert.
Keine Videoqualitäts-, Lautheits- oder Quellenwahrheitsgarantie und kein Release.
