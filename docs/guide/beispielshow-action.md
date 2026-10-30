# Vorbereitete Newsshow als GitHub Action

Workflow **Build prepared example Newsshow**: `.github/workflows/example-newsshow.yml`.

Erstellt eine deutsche Beispielsendung der Redaktion **Allgemein**, Show-ID `main`, aus drei festen Beiträgen in `tests/fixtures/example-show.json`. Die Texte erklären das Format und behaupten keine aktuellen Ereignisse. Es gibt keine Live-Feed-, KI-API-, GPU- oder Telegramnutzung. Nach Paketinstallation bleibt die eigentliche Produktion ohne Netzwerkzugriff.

## Start und Ergebnis

Die erste Produktion startet auf `Full-featured-Newsoutlet` beim Push der Workflow-/Beispieldateien. Änderungen an diesen Dateien lösen erneut einen Lauf aus. Zusätzlich ist `workflow_dispatch` vorgesehen. GitHub zeigt neue manuell startbare Workflows je nach Verfügbarkeit auf dem Defaultbranch möglicherweise noch nicht im Actions-Menü an; für diesen reinen Entwicklungsbranch ist deshalb der eingeschränkte Push-Trigger enthalten. Es wird nichts nach `main` übernommen.

Im fertigen Lauf das Artefakt **newsshow-allgemein-example-<run-id>** herunterladen und entpacken:

- `main/latest.mp4`: vollständige Vorschau mit lokaler deutscher eSpeak-NG-Stimme und vorhandener Darstellung.
- `main/preview.png`, Sprechertext und Untertitel; `main/index.html` als einfacher lokaler Player.
- `archive/JJJJ/MM/TT/main/<produktion>/example-de.mp4`: datiertes Archiv der gekennzeichneten Ausgabe.
- `example-manifest.json`: Beispielstatus, Sprache, Archivpfad, Dauer und SHA-256-Prüfsumme.

**AI steht durchgehend rechts unten im Video**, auch im Vorschaubild. Archivkopien enthalten dieselbe gekennzeichnete Datei. Die Action aktualisiert zusätzlich die Repository-Demo unter `demos/newsshow-demo.*` ausschließlich auf `Full-featured-Newsoutlet`. Dafür hat sie Repository-Schreibrechte und nutzt den automatisch bereitgestellten Actions-Token. Sie verändert weder main noch Pages oder Social Media; zusätzliche Secrets sind nicht erforderlich.

GitHub-Artefakte werden nach 30 Tagen entfernt. Sie sind ein Transportpaket, kein dauerhaft betriebener Archivspeicher. Für langfristige Aufbewahrung das enthaltene Datumsarchiv auf persistenten Speicher übernehmen. Eine automatische Einbindung als vorinstalliertes Startvideo ist noch eine separate Installationsaufgabe.

## Lokaler Aufruf

Python-Abhängigkeiten aus `requirements.txt` und Pillow installieren; FFmpeg/ffprobe, eSpeak-NG sowie DejaVu-Schriften müssen vorhanden sein:

```bash
python3 scripts/build_example_show.py --output-root out/example-show
```

Die Systempakete werden im Ubuntu-GitHub-Runner automatisch installiert. Es werden keine Piper-Modelle heruntergeladen. Vorhandene Produktionskonfiguration wird nicht verändert. Der Beispielbuilder nutzt den bestehenden Renderer mit einer klar begrenzten Fixture-Eingabe, prüft Audio/Video und brennt das Pflichtlabel in einer abschließenden Stufe ein.

## Anzeige im Repository

Die README zeigt **Newsshow-Demo** mit anklickbarem Vorschaubild und MP4-Link. `scripts/export_example_demo.py` prüft die Video-Prüfsumme und übernimmt ausschließlich die feste Beispielsendung. Folgeproduktionen aktualisieren denselben Demodateinamen. Das datierte Archiv bleibt im jeweiligen Artefakt erhalten; die README-Demo ist nur die aktuelle Vorschau.
