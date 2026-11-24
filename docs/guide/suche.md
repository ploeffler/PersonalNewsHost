# Suche

`search.html` durchsucht Beiträge und Sendungen vollständig im Browser, ohne Serveraufruf und ohne externen Dienst.

* **Index:** `search-index.json`, bei jedem RSS-Lauf und jeder Sendung neu erzeugt (`scripts/search_index.py`). Enthalten sind Titel, Kurztext, Rubrik bzw. Sendung, Quelle, Datum und Link.
* **Größenlimit:** `search.max_bytes` (Standard 1 000 000, Minimum 10 000). Wird es überschritten, entfallen zuerst die ältesten Einträge; der Index trägt dann `"truncated": true`.
* **Abschalten:** `"search": {"enabled": false}` – dann wird kein Index erzeugt.
* **Suchverhalten:** Groß-/Kleinschreibung und Umlaute sind egal (`Bürgermeister` = `buergermeister`); alle Suchwörter müssen vorkommen; Titeltreffer zählen stärker.
* **Sicherheit:** Treffer werden per `textContent` ausgegeben, Links nur für `http(s)` und relative Pfade.
