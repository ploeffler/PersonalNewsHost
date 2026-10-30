# Datenschutz – Arbeitsstand für T073

Die Anwendung verarbeitet öffentliche Feed- und Artikelinhalte einschließlich Quellenreferenzen. RSS-, Artikel- und Medienabrufe sowie Paket-/Modelldownloads stellen Verbindungen zu externen Servern her. Optionaler Telegramversand übermittelt die ausgewählten Texte und Medien an Telegram.

Secrets gehören ausschließlich in die Laufzeitumgebung bzw. GitHub Secrets. Cachedateien und private Konfigurationen dürfen nicht als Website oder öffentliche Artefakte veröffentlicht werden. Die technische Durchsetzung und die Prüfung bestehender Artefakte werden mit T073 vervollständigt; diese Bestandsnotiz bestätigt noch keinen Sicherheitsabschluss.

## Impressumsvorlage – vor Veröffentlichung durch Betreiber auszufüllen

- Betreiber / Organisation: [eintragen]
- Anschrift: [eintragen]
- Kontakt: [eintragen]
- Redaktionell verantwortlich: [eintragen]
- Weitere erforderliche Angaben: [durch Betreiber ergänzen]

Dies ist eine Vorlage, kein bereits ausgefülltes Impressum. Personenbezogene Betreiberangaben werden ausschließlich bewusst durch den Betreiber veröffentlicht. Keine Versionsfreigabe oder Wiki-Veröffentlichung.

## Technische Grenzen und Prüfungen von T073

- Die öffentlichen Vorlagen [Datenschutz](../datenschutz.html) und [Impressum](../impressum.html) sind verlinkt; Betreiber müssen sie vor öffentlichem Betrieb vervollständigen. Das System ergänzt keine privaten Betreiberangaben automatisch.
- `scripts/security_checks.py` prüft veröffentlichte Dateien auf bekannte Schlüssel-/URL-Muster, private Zustandsdateien, ausbrechende Symlinks und erkannte Tracker. Es scannt auch große Dateien in Blöcken. Ein erkannter Befund stoppt den Upload; dies gilt auch bei einem `always()`-Artefaktpfad.
- Private Konfigurationsfelder werden vor weiteren Produktionsschritten für GitHub-Logs maskiert. Feed-Zugangsdaten und Querystrings werden nicht in den Video-Quellenhinweis geschrieben. Fehler beim Feedabruf geben nur die Fehlerklasse aus.
- Sämtliche Actions verwenden überprüfte Commit-SHAs; direkte Python-Pakete sind über die versionierten Requirements und globale Pip-Constraints festgelegt. Das ist kein vollständiger Hash-Lock aller transitiven, System- oder Modellabhängigkeiten. Experimentelle Modelljobs wurden für T073 nicht ausgeführt.
- Sicherheitsprüfungen erkennen keine beliebigen personenbezogenen Angaben in freiem Nachrichtentext. Öffentliche Quelleninhalte bleiben redaktionelle Daten; private Inhalte gehören nicht in die öffentlichen Feeds. Die Prüfung ist keine rechtliche Freigabe und keine Garantie für alle unbekannten Secretformate.

Wiki-Synchronisierung und Versionsfreigabe bleiben vom Abschluss dieser Aufgabe getrennt.
