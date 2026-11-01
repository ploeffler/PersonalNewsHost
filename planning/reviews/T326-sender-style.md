# T326 — lokaler Senderstil-Editor

Vorgezogener eigenständig nutzbarer Einstieg: geschützte lokale Senderseite mit initialem
Outletentwurf und späterem Button, CI-Entwürfen, aktiver Version, Historie/Export,
URL-CSS-Recherche und atomarer Vorschau-Outbox für alle 14 Stile.

T216–T218 und die globale Verwaltung behalten ihre restlichen Integrationsumfänge.
Kein stiller Umbau der bestehenden Produktion oder Veröffentlichung. Für eigene
Bildvorschauen ist ein dedizierter serverseitiger OpenAI-Adapter vorhanden; keine
Account-/Preisbehauptung, Zugriff und Budget müssen eingerichtet und freigegeben sein.

Sicherheits- und Persistenzgrenzen: private Dateien, Loopback, Sitzung/Host/Origin/CSRF,
öffentliche DNS-geprüfte Rechercheverbindungen, begrenzte passive Inhalte, nur bestätigte
CI-Felder im Prompt, Compare-and-swap bei Entwürfen, atomare Version/Job-Anlage,
konservative persistente Reservierungen, unklare Jobs ohne automatische API-Wiederholung.

Prüfungen: neue Unit-/Integrationsfälle für CI, URL-Recherche, Adapter und geschützte APIs;
realer Browserablauf gegen lokalen Server (kein Cloudaufruf), Mobilansicht und Screenshot.
Gesamtlauf und Commitnachweis werden im Aufgabenreview festgehalten. Die externe Images-
Schnittstelle ist dokumentiert und mit synthetischer Antwort getestet, nicht bezahlt live
aufgerufen. Kein Versionsrelease oder Wiki-Publish.

Lokaler Gesamtlauf: 434 Tests bestanden (32 neue CI-/Recherche-/Adapter-/API-Fälle),
Ruff F821/F822/F823 und JS-Syntax bestanden. Realer Browser: Anmeldung, Setupentwurf,
URL-Vorschlag anwenden, Speichern/Reload, Übernahme, 14 Jobs, unveränderte Wiederholung,
Button, konkurrierende Bearbeitung, Mobilansicht, Abmeldung. Reale passive URL-Recherche
gegen python.org lieferte vier Quellen und beobachtete Farben/Schriften ohne Warnungen.
Keine kostenpflichtigen API-Aufrufe oder Zugangsdaten im Test.
