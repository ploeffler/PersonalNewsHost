# T323: Vorgezogene Provider-Einrichtungsabläufe

Ausdrücklicher Nutzerauftrag: „die einrichtungsabläufe sind jetzt dran“.
Als eigenständiger Dokumentationsauftrag in 0.2 eingeplant; T102 und T320–T322
bleiben mit Anbieterbewertung, Adaptern, geschützter Verwaltung und UI-Abnahme offen.
Der Tag v0.1 bleibt unverändert. Kein neuer Release-Tag oder Wiki-Push.

Die Anleitung deckt Mock, lokale Produktionsstimmen und Medienpfade sowie Ollama,
llama.cpp, LocalAI, ComfyUI, stable-diffusion.cpp, Docker Model Runner, Gemini,
Groq, Mistral, OpenAI, Anthropic, BFL und Runway ab. Jeder externe Kandidat bleibt
klar als nicht implementierter PNH-Adapter markiert. Einrichtung beim Anbieter,
Modell-/Endpointprüfung, Kosten, Secrets, Container-Netzwerk und Fehlerhilfe sind
von der künftigen PNH-Aktivierung getrennt. Veraltete Runtime-Angaben korrigiert.

Offizielle Quellen am 01.11.2026 geöffnet und im Dokument verlinkt; keine
Modellverfügbarkeit, regionalen Free-Tiers oder dauerhaften Preise zugesichert.
OpenAI-Abschnitt nach OpenAI Docs Skill und offizieller Dokumentation verfasst.

Prüfungen: Mock-Konfiguration gültig; CLI zweimal ohne Provider-Netzwerk ausgeführt,
zweiter Lauf Cachetreffer. Secret-Scan, lokale Markdownlinks, diff --check und
sechs Dokumentations-Release-Tests bestanden. Keine Cloudschlüssel abgefragt,
keine Konten angelegt, keine Dienste installiert und keine echte Generierung.
Externe Installationsbefehle sind dokumentiert, nicht auf diesem Rechner erprobt.
Ein unabhängiger Review der Benutzeranleitung bleibt erforderlich.
