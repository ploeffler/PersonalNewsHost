# Provider-Laufzeit: Offline-Grundlage für 0.1

`scripts/provider_runtime.py` ergänzt die bisherige planende Registry um einen separat testbaren Ausführungsvertrag. Noch keine reguläre Sendung verwendet automatisch diese neue Laufzeit. Es gibt keine HTTP-Adapter und keine kostenpflichtige Ausführung.

## Fähigkeiten

- Providerarten: Textgenerierung, Textanalyse, Fact-Check-Quelle, Videogenerierung, Avatarvideo und TTS.
- Deterministische Mocks für jede Art. Textmocks liefern einen Quelltextauszug; andere Mocks ausschließlich ausdrücklich als `mock` markierte Referenzen, keine abspielbaren Medien und keine Faktenbestätigung.
- Registrierung mit eindeutiger ID, Revision und passender Providerart.
- Strikte JSON-Antwortprüfung. Ungültige Antworten werden nicht zwischengespeichert. Fehlermeldungen geben weder Inhalte noch Validatorwerte aus.
- Fehlerklassen für Timeout, Quota, Authentifizierung, Ablehnung und ungültige Antworten; begrenzte Wiederholung und ein expliziter Fallback.
- Lokaler SQLite-Cache mit Schlüssel aus Namespace, Providerrevision, Modell, Aufgabe, Promptversion, erlaubten Eingaben und Antwortschema. Änderung eines dieser Bestandteile erzeugt einen neuen Eintrag.
- Eine SQLite-Schreibtransaktion serialisiert Cachemisses auch zwischen mehreren Prozessen. Identische erfolgreiche Aufträge werden einmal berechnet; fehlgeschlagene Berechnungen rollen zurück. Beschädigte Cacheeinträge werden erneut berechnet.

## Beispiel

```python
from scripts.provider_runtime import Cache, Runtime, MockProvider, Request

runtime = Runtime(Cache('state/provider-cache.sqlite'), namespace='redaktion-a')
runtime.register(MockProvider('local-text', 'text_generation'))
result = runtime.run('local-text', Request(
    kind='text_generation', task='summary', model='extractive',
    prompt_version='v1',
    payload={'text': 'Eine belegte Aussage.', 'source_id': 'artikel-1'},
))
```

`namespace` trennt Cacheeinträge verschiedener Redaktionen. Das ersetzt noch keine Mandanten- oder Dateisystem-Zugriffskontrolle. Der Cache kann Quelltextauszüge enthalten und muss unter einem geschützten persistenten Datenpfad liegen; keine Aufnahme in öffentlich ausgelieferte Dateien.

## Eingaben und Grenzen

Pro Providerart gibt es eine feste Allowlist skalarer Felder. Andere Felder werden vor Ausführung entfernt; verschachtelte Inhalte in erlaubten Feldern werden abgelehnt. Erkennbare API-Key-/Bearer-Muster und ausdrücklich übergebene Secretwerte werden in Payload, Anfragemetadaten und Antworten geprüft. Eine solche Prüfung erkennt nicht garantiert alle möglichen Geheimnisse.

Feedtext bleibt Datenmaterial, auch wenn er wie eine Anweisung aussieht. Die Laufzeit führt keine Modellantworten, Werkzeuge oder Dateipfade aus. Das ist keine Behauptung, ein echtes Sprachmodell könne dadurch niemals auf eingebettete Anweisungen reagieren. Gezielte Tests mit realen Modellen und die vollständigen aufgabenspezifischen Ausgabeschemata folgen noch.

Timeouts werden als Deadline-Budget an den Adapter übergeben. Ein Adapter muss seine tatsächlichen I/O-Zugriffe begrenzen; die Laufzeit kann beliebigen blockierenden Python-Code nicht sicher abbrechen. Derzeit simulieren Mocks Timeoutfehler. Auch Rate-Limits, Backoff, dauerhafte Kostenreservierung, Providerkonfiguration aus config.json und Actions-Cachepersistenz sind noch nicht integriert. Kostenpflichtige Provider werden deshalb **vor jedem Aufruf und auch vor Cachezugriff abgewiesen**; es gibt keine stillschweigende Freischaltung durch Konfiguration.

Diese Grundlage ist noch keine vollständige Abnahme von T100/T101/T103/T104/T130/T135.
