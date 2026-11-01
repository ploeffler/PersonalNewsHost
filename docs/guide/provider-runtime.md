# Provider-Laufzeit und Konfiguration

`scripts/provider_runtime.py` ist die getestete Mock-Laufzeit aus v0.1. Optionale Analysezuordnungen sind im Generator angebunden; ohne Zuordnung bleibt die Analyse aus. Es gibt keine HTTP-Adapter für reale Anbieter.

Für konkrete Schritte nach der Anbieterauswahl siehe [Provider einrichten](provider-einrichtung.md).

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

Feedtext bleibt Datenmaterial, auch wenn er wie eine Anweisung aussieht. Die Laufzeit führt keine Modellantworten, Werkzeuge oder Dateipfade aus. Das ist keine Behauptung, ein echtes Sprachmodell könne dadurch niemals auf eingebettete Anweisungen reagieren. Alle sieben aufgabenspezifischen Schemata und feindliche Feed-Fixtures sind getestet. Anweisungsähnlicher Quelltext bleibt inert erhalten; ein Schutz echter Sprachmodelle ist nicht nachgewiesen.

Timeouts werden als Deadline-Budget an den Adapter übergeben. Die Runtime kann beliebigen blockierenden Python-Code nicht sicher abbrechen. Begrenzte Wiederholungen, Prozess-Rate-Limits in der Registry, persistente Mockreservierungen, Konfigurationsvalidierung und Actions-Cachewiederverwendung sind integriert. Reale kostenpflichtige Adapter bleiben nicht implementiert. Die direkte Analyse-Testfactory kann ausschließlich lokale Mockkosten nach explizitem Budget-Opt-in simulieren.

T100/T101/T103/T104/T130/T135 sind für den dokumentierten Mock-Umfang abgenommen. Details und Grenzen stehen in den jeweiligen Nachweisen unter `planning/reviews/` sowie in der [Abnahme 0.1](abnahme-0.1.md).

## Konfiguration und Produktionsanbindung in 0.1

Die oben beschriebene anfängliche Offline-Grundlage wurde für den 0.1-Meilenstein erweitert. Maßgeblich sind diese Ergänzungen:

- `providers`: Liste mit `id`, `kind`, `adapter: "mock"`, `enabled`, `secret_name`, `endpoint`, `model`, `timeout_s`, `retries`, `rate_limit` (Anfragen/Minute), `cost_model`, `priority` und `fallback_to`. `priority` bestimmt in der Registry die Auswahl aktivierter Anbieter (kleinere Werte zuerst); `provider_tasks` ordnet Analysen explizit zu. `endpoint` wird von Mocks nicht aufgerufen.
- `provider_tasks`: explizite Zuordnung der sieben Analyseaufgaben zu aktivierten Textanalyse-Mocks. Ohne Zuordnung verändert sich die bisherige Produktion nicht. Ergebnisse landen in `provider-analysis.json`, nie ungeprüft im freigegebenen Sprechertext.
- `provider_budgets`: `allow_paid`, `monthly_budget_eur`, `per_run_budget_eur`, `unit_limits`. Kostenstandard 0. `cost_model.max_cost_eur` und `cost_model.units` simulieren konservative Kosten/Einheiten je Mockversuch. Das ist keine Behauptung echter Tokenmessung.
- `state/providers/`: Cache, dauerhafte Kostenreservierungen und Auditlog. Die gemeinsame Produktionsnamespace `installation` verhindert getrennte Monatsbudgets je Show. Dateizugriff auf SQLite ist auf den Dienstbenutzer begrenzt.
- Kosten werden vor jedem Versuch atomar reserviert. Fehlgeschlagene oder unklare Versuche bleiben angerechnet; gleiche erfolgreiche Cachetreffer erzeugen keine neue Reservierung. Quota/Budgetfehler aktivieren den expliziten Fallback.
- Nur verifizierbare **Mockkosten** können nach ausdrücklichem Opt-in simuliert werden. Reale kostenpflichtige Adapter sind weiterhin nicht enthalten. Direkte Runtime-Erweiterungen sind vertrauenswürdiger Anwendungscode, keine Sandbox.
- Der News-Workflow erhält konservative Nutzungsdaten im Jobreport und stellt den optionalen Providerzustand über Actions-Cache wieder her. Abgebrochene Runner können Cache-Sicherungen verlieren; deshalb keine Garantie einer externen Kostengrenze über Actions, solange echte Adapter nicht separat abgesichert sind.

Beispiel (in eine vollständige Konfiguration einfügen):

```json
{
  "providers": [{"id": "local-analysis", "kind": "text_analysis", "adapter": "mock", "enabled": true, "model": "deterministic"}],
  "provider_tasks": {"summary": "local-analysis", "classification": "local-analysis"},
  "provider_budgets": {"allow_paid": false, "monthly_budget_eur": 0, "per_run_budget_eur": 0, "unit_limits": {}}
}
```

Unbekannte Provider, doppelte IDs, inkompatible oder zyklische Fallbacks und deaktivierte Analyserouten werden vor Produktion abgewiesen. Die Analyse-Schemata stehen in `scripts/analysis_tasks.py`. Leere Entitäten, `general`, Score 0 und `assessed: false` sind konservative Baselines, keine scheinbar gemessenen Modellurteile.
