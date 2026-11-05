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

## Erneute Einreichung – 5. November 2026

Die ursprüngliche Einreichung wurde wegen nachträglicher Änderungen im Prüfumfang
zurückgegeben. Diese Einreichung umfasst den aktuellen integrierten Senderstilstand
einschließlich der ausdrücklichen Neubeauftragung mit aktueller Providerfreigabe.
Es wurden in diesem Durchgang keine Produktfunktionen geändert.

Getestete Codebasis: `7f4cfd2278b00d1522a0d4b91571c0556dde7cfc`; anschließend
Fast-forward auf `bcd8247` mit ausschließlich Board-/Mirroränderungen.

- `python3 scripts/check_repository.py`: 439 Tests ausgeführt; 438 bestanden,
  ein Umgebungsfehler, weil die Sandbox das Erzeugen eines Sockets verbietet
  (`test_network_guard_denies_tcp_udp_and_dns_and_restores`). Python-Syntax,
  Secretprüfung und lokale Markdownlinks bestanden. Video-Fixtures wurden erzeugt.
- `python3 -m unittest discover -s tests -p test_repository_checks.py` außerhalb
  dieser Sandbox: alle vier Tests bestanden, einschließlich des betroffenen Tests.
  Dessen eigener Netzwerkblocker blieb aktiv. Somit sind alle 439 Testfälle durch
  den Gesamtlauf plus die isolierte Wiederholung erfolgreich abgedeckt; ein einziger
  vollständig grüner Gesamtlauf wird hier nicht behauptet.
- 36 gezielte Senderstil-/Recherche-/Vorschau-/API-Tests bestanden.
- Nach dem Fast-forward: 11 Koordinationstests und 6 Release-Gating-Tests bestanden.
- `config.json`, `config.example.json`, `config.shows.example.json` gültig;
  `git diff --check` ohne Befund.

Node.js und Ruff sind in dieser Umgebung nicht installiert. JavaScript-, Ruff- und
Browserprüfungen wurden in diesem Durchgang nicht erneut ausgeführt; die oben
genannten früheren Nachweise bleiben historische Nachweise. Kein kostenpflichtiger
Provideraufruf, keine Telegram-Liveveröffentlichung und keine Versionsfreigabe.
Der erneut eingereichte Commit braucht eine unabhängige Prüfung; der einreichende
Client darf ihn nicht selbst abschließen.
