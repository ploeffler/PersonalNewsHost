# Sitemap, Metadaten und Teilen

Bei jedem RSS-Lauf und jeder Sendung (`scripts/site_meta.py`) entstehen:

* **`sitemap.xml`** mit Startseite, Archiv, Suche sowie allen Artikel-, Rubriken- und Sendungsseiten (auch den Folgeseiten der Paginierung). Höchstens 50 000 Einträge.
* **`robots.txt`**: alles erlaubt, Verweis auf die Sitemap.
* **Seitenmetadaten** zwischen den Markern `pnh:meta` im `<head>`: kanonische URL, Open Graph, Twitter Card.
* **Strukturierte Daten (JSON-LD):** `NewsArticle` auf Artikelseiten, `CollectionPage` auf Rubriken und Sendungen, `WebSite` und – sobald eine Sendung vorliegt – `VideoObject` auf der Startseite.

Die Basis-Adresse steht in `site.base_url` (Konfiguration) oder in der Umgebungsvariable `PNH_BASE_URL`; ohne beides gilt die Adresse der Projektseite. Nur `http(s)`-Adressen werden akzeptiert. Der Metadaten-Block wird bei jedem Lauf ersetzt, Seiten außerhalb der Liste (Konfiguration, Studio) bleiben unverändert.
