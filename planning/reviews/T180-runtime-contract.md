# T180: Gemeinsamer lokaler Betriebsvertrag

Ein gemeinsamer CLI-Einstieg definiert inspect, due, produce und serve-preview
für Linux und ein späteres /app-Containerlayout. Modelle, Medien, privater Zustand,
interne Produktionen und öffentlich ausgewählte Dateien sind getrennt. Der
bestehende Producer und Scheduler werden wiederverwendet; kein GitHub- oder
Secret-Kontext erforderlich. Vorschau ausschließlich Loopback und ohne Symlinks.

Acht Tests prüfen relative Pfadgleichheit, unabhängige Terminprüfung, Delegation
an isolierte Produktion, frühe Konfigurationsfehler, Vorschauadresse/-pfad,
Symlink-/Portverweigerung, secretsfreies inspect und redigierte CLI-Fehler.
Integrationsergebnis im Aufgabenreview. Reale Linux-/Containerinstallation,
Dauerbetrieb, TLS und Pflichtarchiv bleiben den jeweiligen Folgeaufgaben zugeordnet.
