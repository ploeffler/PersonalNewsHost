# KI-Kennzeichnung

Sendung und Seiten sind deutlich als „Automatisch erstellt mit KI-Unterstützung" gekennzeichnet (`scripts/ai_disclosure.py`, bei jedem RSS-Lauf und jeder Sendung):

* **Startseite:** Hinweisblock direkt unter dem Video mit Link auf „Über diese Sendung".
* **Artikelseiten:** Hinweisblock mit Abrufzeit (Zeit der Sendung, für die die Quellen abgerufen wurden), Link auf „Über diese Sendung"; Quellen und Link zum Original stehen auf der Seite (T020).
* **`ueber-diese-sendung.html`:** Funktionsweise, Grenzen und Korrekturkontakt. Der Kontakt steht in `about.correction_contact` (Konfiguration); ohne Eintrag verweist die Seite auf das Impressum.
* **Prüfung:** `missing_disclosure(docs)` nennt Startseite und Artikelseiten ohne Kennzeichnung.

Die Kennzeichnung im Videobild (rechts unten) folgt mit T280, die von synthetischen Stimmen, Avataren und Clips mit T145 und T167.
