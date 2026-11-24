# Bildquellen und Lizenzen

Jedes Bild einer Sendung hat einen Nachweis in `media-credits.json` (Herkunft, Lizenzstatus, Lizenz, Rechteinhaber, Grundlage). Der Nachweis erscheint auf der Artikelseite („Bild: …") und als Zeile im Abspann.

| Herkunft (`image_origin`) | Status | Verwendung |
| --- | --- | --- |
| `generated_graphic` | `licensed` („eigene Grafik") | immer; automatisch erzeugte Nachrichtentafel |
| `commons` | `licensed` | Wikimedia Commons, nur Public Domain/CC0 (aus den Commons-Metadaten geprüft) |
| `publisher_image` | `licensed` | nur wenn die Quelle unter `media.licensed_sources` mit Lizenz freigegeben ist |
| `publisher_image` | `unverified` | **nicht verwendet** (Standard); Ersatz ist Commons oder die Nachrichtentafel |

## Einstellungen (`media`)

* `license_policy`: `"strict"` (Standard) oder `"record_only"`. Mit `record_only` werden Bilder aus Artikelmetadaten und RSS weiter verwendet; der fehlende Nachweis steht dann als „Lizenz nicht nachgewiesen" auf der Artikelseite.
* `licensed_sources`: Liste freigegebener Quellen, z. B. `{"host": "images.example.org", "license": "CC BY 4.0", "holder": "Beispiel Agentur"}`. Ein Eintrag ohne `license` gilt nicht als Freigabe. Subdomains sind eingeschlossen.

## Datenmodell

Pflichtfelder je Eintrag: `source`, `image_origin`, `license_status`; bei `licensed` zusätzlich `license`. Fehlt etwas, bricht die Sendung ab (`media_rights.validate_credits`). Verworfene Bilder stehen als `rejected_publisher_image`. Das Verhalten bei Videos in RSS-Anhängen ist dasselbe.

Hinweis: Auch freigegebene Bilder ersetzen keine rechtliche Prüfung durch den Betreiber.
