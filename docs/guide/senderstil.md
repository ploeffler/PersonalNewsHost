# Senderstil und eigene Stilvorschauen

Der lokale Senderstil-Editor ist ein vorgezogener Einstieg für die Corporate Identity
(CI) eines Outlets. Er bietet Ersteinrichtung, spätere Bearbeitung über die Senderseite,
passive URL-Recherche und automatische Bildvorschauaufträge nach Übernahme.
Die allgemeine geschützte Gesamtverwaltung und die Übernahme in alle Produktionsrenderer
bleiben eigene Aufgaben (T193, T216–T218, T250, T290). Dieser Editor aktiviert keine
Veröffentlichung und ändert weder `config.json` noch vorhandene Sendungen.

## Start

Im ausgecheckten Repository mit der vorhandenen Projekt-Python-Umgebung starten:

```sh
python3 scripts/sender_style_server.py
```

Der Prozess bindet ausschließlich `127.0.0.1:8766`. Im Browser
<http://127.0.0.1:8766> öffnen und mit dem beim Start im Terminal angezeigten temporären
Passwort anmelden. Alternativ `PNH_STYLE_ADMIN_PASSWORD` über die geschützte
Laufzeitumgebung setzen (mindestens 16 Zeichen); nicht in Git oder öffentliche
Konfiguration schreiben. Ohne festes Passwort wird beim Neustart ein neues erzeugt.

Der erste Start übernimmt erlaubte Outletangaben aus `config.json` als Entwurf:
Titel, Formatbeschreibung, Zielgruppe, Sprache und Ton aus `editorial_identity`, soweit
vorhanden. Provider-Secrets und sonstige Konfiguration werden nicht kopiert. Ein bereits
bearbeiteter Entwurf bleibt beim Neustart erhalten. Der Editor benötigt Pillow zusätzlich
zum vorhandenen Python-Kern; der [Linux-Installer](linux-installation.md) richtet dies in
seiner unterstützten Umgebung ein.

Dieser vorgezogene Editor ist kein öffentlicher Admin-Dienst. Für einen entfernten
Linux-Rechner ausschließlich einen eigenen geschützten SSH-Tunnel auf Loopback nutzen;
kein Binden an `0.0.0.0`, kein öffentliches Portforwarding. Die spätere gemeinsame
HTTPS-Verwaltung ist hierdurch nicht ersetzt.

## Ablauf auf der Senderseite

1. **Senderstil erstellen/bearbeiten** öffnet denselben Editor bei der Ersteinrichtung
   und später erneut.
2. Beschreibung, Zielgruppe, Sprache/Ton, Bildsprache, Farbpalette, Schriften,
   Branding, Studio-/Avatarvorgaben und Vorschauformat bearbeiten. Farbfelder und eine
   Entwurfsübersicht helfen bei der Prüfung; Schriftlisten sind Vorgaben, keine automatisch
   heruntergeladenen oder lizenzierten Fonts.
3. Optional eine öffentliche URL ohne Queryparameter oder Fragment recherchieren.
   Ergebnis, Quelladressen und Abrufzeitpunkte prüfen. „Farben und Schrift in Entwurf
   übernehmen“ ändert den Entwurf, niemals die aktive CI. Seitentitel und Beschreibung
   bleiben zitiertes Recherchematerial; sie werden nicht automatisch in Prompts übernommen.
4. **Entwurf speichern** erhält die laufende aktive Version. **Basisstil übernehmen &
   Vorschauen anlegen** aktiviert die geprüfte CI und erzeugt eine Serie für alle
   14 Bibliotheksstile einschließlich Stop-Motion-Holzgliederfigur.
5. Provider-/Budgetstatus und Ergebnisse erscheinen auf der Senderseite. Fehlende
   Voraussetzungen halten die Aufträge sichtbar wartend. Nach Einrichtung erneut
   übernehmen, wenn sich die Provider-Vorgaben geändert haben; ein unveränderter
   Kontext verwendet dieselbe Serie. Einzelne wartende Jobs lassen sich erneut prüfen.

Die Vorschauen verwenden ein gemeinsames Vergleichsmotiv (Reporterin bzw. Figur am Fluss
mit Brücke), den jeweiligen Bibliotheksstil und die freigegebene Sender-CI. Das Format gilt
für die gesamte Serie. Sie sind KI-generierte Einzelbilder, keine echten Nachrichtenbilder
und kein Nachweis für Animations-, Video- oder Lipsyncqualität.

**Aktive Vorlage exportieren** liefert einen JSON-Snapshot für spätere Integration.
`scripts/sender_style.py:effective_style` stellt den Vererbungsvertrag für Senderstandard
und explizite lokale Überschreibungen bereit. Die aktuelle Sendungsproduktion konsumiert
diesen Export noch nicht automatisch. Gespeicherte Produktionssnapshots und fertige Videos
werden durch spätere CI-Änderungen nicht umgeschrieben.

## Bildprovider und Kosten

Ohne Bildprovider funktioniert die gesamte CI-Bearbeitung und Übernahme; die generischen
[mitgelieferten Stilbeispiele](../../assets/style-examples/index.html) bleiben sichtbar.
Der erste ausführbare Adapter dieses Editors ist die OpenAI Images API. Zugangsdaten
werden ausschließlich serverseitig aus `PNH_STYLE_IMAGE_API_KEY` gelesen, niemals im
Browser eingegeben, im Auftrag gespeichert oder an die URL-Recherche weitergegeben.

Vor einem kostenpflichtigen Lauf über die eigene Laufzeitumgebung konfigurieren:

- `PNH_STYLE_IMAGE_PROVIDER=openai`
- `PNH_STYLE_IMAGE_MODEL`: eigener freigeschalteter GPT-Image-Modellname; Vorgabe `gpt-image-2`.
- `PNH_STYLE_IMAGE_API_KEY`: eigener API-Schlüssel, nur als Secret.
- `PNH_STYLE_ALLOW_PAID=true`: kostenpflichtige Vorschauen grundsätzlich zulassen.
- `PNH_STYLE_RESERVE_EUR`: positive konservative Reservierung je Bild.
- `PNH_STYLE_BATCH_EUR` und `PNH_STYLE_MONTHLY_EUR`: Serien- und Monatslimit in EUR.

Alle Geldwerte sind standardmäßig **0**. Es gibt keine hinterlegte Preisbehauptung.
Der Betreiber muss aktuelle Modellpreise, Währungsumrechnung und seine Sicherheitsreserve
prüfen. Die lokale Reservierung begrenzt Versuche auf Basis dieser Betreiberangabe;
sie ist keine Messung und keine Garantie der externen Rechnung. Zusätzlich ein passendes
Limit im Providerkonto setzen. Im Editor wird die Reservierung für die ganze Serie vorab
angezeigt; die Checkbox gibt sie bei **Übernehmen** für diesen Kontext frei. Ohne diese
Freigabe werden keine Bildaufrufe ausgeführt.

Verwendet wird die feste HTTPS-API für ein PNG je Job, Qualität `low`, ohne automatische
HTTP-Wiederholungen oder Weiterleitungen. Bilder werden direkt aus der Base64-Antwort
validiert; externe Ergebnis-URLs werden nicht abgerufen. Der konkrete Account muss das
gewählte Modell unterstützen. Schnittstelle geprüft am 1. November 2026 anhand der
[offiziellen Images-Referenz](https://developers.openai.com/api/reference/resources/images/methods/generate).
Andere Bild- oder Videoprovider sind durch diesen Editor noch nicht angebunden.

## Persistenz, Wiederaufnahme und Datenschutz

Private Zustände liegen in `state/sender-style/` (ignoriert durch Git): SQLite für
Entwurf/Versionen/Serien/Jobs, separate konservative Budgetreservierungen und `images/`.
Verzeichnisrechte sind auf den Betriebssystembenutzer beschränkt; Metadaten und Bilder
werden nur nach Anmeldung ausgeliefert. Ein Prozess-Lock verhindert zwei konkurrierende
Editorprozesse für dasselbe Verzeichnis. `--state` und `--port` erlauben getrennte Instanzen.
Ein bereits anderweitig veränderter Entwurf erzeugt einen Konflikt statt stiller Überschreibung.

Eine Übernahme aktiviert Version und legt die Aufträge in derselben SQLite-Transaktion an.
Sender-CI, Bibliotheksversion/Inhalt, Provider/Modell, Format und Promptversion werden als
unveränderlicher Kontext gespeichert. Wiederholtes Übernehmen erzeugt keine zweite Serie
für identische Angaben. Frühere CI-Versionen können wieder als Entwurf geladen werden;
ältere Vorschauen bleiben sichtbar einer früheren Version zugeordnet.

Fehlgeschlagene oder unklare API-Versuche behalten ihre Reservierung. Nach einem Abbruch
werden laufende Jobs ohne bereits vollständig gespeichertes Bild als **unklar** gehalten,
nie automatisch erneut bezahlt. Ein bereits dauerhaft gespeichertes und validiertes PNG
wird ohne zweiten API-Aufruf dem vorhandenen Auftrag zugeordnet. Vor einer
bewussten Wiederholung die externe Abrechnung prüfen; der Editor weist auf zusätzliche
Kosten hin. Unterbrochene ältere Jobs verändern keine neuere CI-Version. Es gibt keine
automatische Rechnungserstattung und keine behauptete Exactly-once-Garantie über die
externe API hinweg.

URL-Recherche liest höchstens eine HTML-Seite und drei gleichursprüngliche Stylesheets,
mit Größen-, Zeit- und Redirectgrenzen, ohne JavaScript, Anmeldung oder Assetdownloads.
Private, Loopback-, Link-local- und Metadatenadressen werden auch bei DNS-Auflösung und
Weiterleitungen abgelehnt. Nicht erkennbare Gestaltung, Zielgruppe, Haltung und Rechte
bleiben unbekannt. Fremde Websiteinhalte sind Daten, keine ausführbaren Anweisungen.

Eigene Vorschauen bleiben standardmäßig privat. Weder Upload, Git-Commit, Push noch
Veröffentlichung werden automatisch ausgelöst. Die Anmeldung verwendet eine kurzlebige
lokale Sitzung mit HttpOnly/SameSite-Cookie, CSRF- und Origin-/Host-Prüfung. Die HTTP-
Sitzung ist ausschließlich für Loopback bestimmt; ein öffentlicher Produktionsbetrieb
benötigt die spätere gemeinsame HTTPS-/Admin-Integration.


## Wartende Vorschauen mit neuem Provider beauftragen

Ein normaler Wiederholungsversuch verwendet weiterhin den gespeicherten
Provider- und Budgetstand. Nach einer Provider-Einrichtung oder einer neuen
Kostenfreigabe stattdessen **Mit aktueller Providerkonfiguration neu beauftragen**
verwenden. Die Aktion benötigt einen eingerichteten Bildprovider und eine
explizite neue Kostenbestätigung; ohne Freigabe erfolgen keine Aufrufe.

Es entsteht eine verknüpfte vollständige Ersatzserie mit allen Bibliotheksstilen.
Senderstil und Bibliothek stammen aus der ursprünglichen Serie, nicht aus einem
zwischenzeitlich bearbeiteten Entwurf. Alte Bilder, Versuche und Reservierungen
bleiben erhalten; bereits angefallene Kosten werden nicht erstattet oder
zurückgesetzt. Unklare und fehlgeschlagene Versuche vorab in der Abrechnung prüfen.
Laufende Serien können erst nach Abschluss des aktuellen Aufrufs ersetzt werden.
Mehrfaches Bestätigen derselben Neubeauftragung erzeugt keine weiteren Serien.
