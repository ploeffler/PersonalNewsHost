# T181: Wiederholbare Repository-Installation unter Linux

Erster Zielumfang Ubuntu 24.04/x86_64/Python 3.12, Kernabhängigkeiten in eigener
verwalteter .venv-pnh, OS-Voraussetzungen nur prüfen. Keine Systempaketänderung,
Modelldownloads oder Cloudaktivierung durch den Installer. Konfiguration exklusiv
nur bei Fehlen kopieren, bestehende Dateien erhalten. Requirements-Fingerprint
und Importprüfung vermeiden unnötige Neuinstallation; eigene partielle Umgebung
kann nach Fehler erneut aufgebaut werden, fremde/symlinkte Ziele werden verweigert.

Sechs gezielte Tests für Vorprüfung, Daten-/Konfigurationserhalt, Wiederholung,
Configseed, fremde Umgebung, Fehlerwiederholung und geänderte Requirements.
Frischer CI-Smoke installiert Abhängigkeiten, prüft Wiederholung mit Sentineldateien,
rendert reale eSpeak-Sprache aus lokalem Fixturefeed und ruft das Video per HTTP-
Loopback ab. Aktuelle Hostumgebung Ubuntu 26.04/Python 3.14 ist nicht als geprüft
freigegeben und wird nicht verändert. CI-/Gesamtergebnisse im Aufgabenreview.

Keine automatische Veröffentlichung, kein Dienst/HTTPS und keine vollständige
Update-/Rollback-Migration; diese bleiben Folgeaufgaben. Kein Versionsrelease.
