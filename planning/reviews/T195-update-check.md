# T195: Automatische Originalversionsprüfung

Öffentliche Originalquelle fest ploeffler/PersonalNewsHost, keine Fork-origin-
Übernahme und kein Tokenzugriff. Semantische Versionssortierung, bestätigte
Release-Marker/Versionsdateien und optionale GitHub-Releaseflags begrenzen die
Kandidaten. Beobachtete Tagzuordnungen erkennen spätere Verschiebungen.
Private atomare Statusdatei, Schreibersperre, Timeout/Antwortlimits, persistenter
Backoff und Intervallprozess; Runtime-CLI unterstützt check-/watch-updates.
Installierte Checkout- oder optionale Container-Buildidentität wird ausgewiesen.

Vierzehn Tests prüfen Vergleich, alte/gleiche/neue Versionen, Vorab-/Entwurffilter,
Tag-only-Releases, verschobene Tags, Intervall nach Neustart, Offline-/Rate-Limits,
VERSION-Mismatch, private Datenfreiheit, Buildidentität und Watch-Wiederholung.
Gesamtprüfungen und Live-Metadatencheck im Aufgabenreview festgehalten.

Keine Installation oder Code-Fetch in den Checkout. Dienstinstallation folgt
mit T182; T196 implementiert getrennt Migration/Update/Rollback. Keine allgemeine
Kompatibilitäts- oder Signaturgarantie; unbekannte frühere Tagverschiebungen sind
beim Erstkontakt nicht rekonstruierbar. Keine neue Versionsfreigabe.
