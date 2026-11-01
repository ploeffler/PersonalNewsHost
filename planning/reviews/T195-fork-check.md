# T195: Alle Forkbranches prüfen und Rückstände melden

Korrigierter Auftrag: alle Branches eines Forks gegen gleichnamige Branches des
bestätigten Parent/Source prüfen, inklusive ahead/behind, divergenter und fehlender
Gegenstücke. Paginierte API-Listen, Vergleich über konkrete Commitköpfe, branchweise
Fehler statt falsch „aktuell“. Verwalteter Issue mit Fingerprint verhindert
wiederholte Hinweise bei unverändertem Rückstand; Änderungen und Auflösung werden
per Kommentar dokumentiert. Nur explizites --notify schreibt in Issues.

Echter lesender QSSTV-Test: main 4 voraus/36 zurück; blackhole-trial aktuell;
drei fork-eigene Branches und rx-sensitivity nur im Original erkannt. Kein
Live-Schreibzugriff durchgeführt. APIs ohne Redirects, Tokenfehler redigiert.
396 Tests im vollständigen Offline-/Videolauf bestanden, einschließlich
Source-Fork-Randfall, sicherer Namensdarstellung und expliziter Arbeitsbranch-Zuordnung.
Alle 24 Forktests bestehen. Fehlerhafte Zuordnungen
werden nicht als aktuell gemeldet.
Weitere CI-Ergebnisse im Aufgabenreview. Release-Checker bleibt getrennt.

Tagesworkflow Teil des gemeinsam integrierten T196-Umfangs. Er muss im Default-
branch des Forks liegen und Actions/Issues müssen aktiviert sein. GitHub-Zeitpläne
sind nicht minutengenau und können bei Inaktivität deaktiviert werden. E-Mail-
Zustellung hängt von den GitHub-Abonnements ab, keine eigene Mailfunktion.
