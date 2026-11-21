# Moderatoren und Studio-Varianten

Moderatoren (`hosts`) und Studios (`studios`) werden einmal in der Konfiguration angelegt und von Shows über ihre ID verwendet. So können mehrere Shows unterschiedlich aussehen und klingen, ohne dass Einstellungen kopiert werden.

```json
"hosts": {
  "newshost": {"name": "NewsHost", "portrait": "assets/presenter.png",
               "voice_model": "de_DE-thorsten-high", "voice": "de", "voice_pitch_semitones": -1.5},
  "tech": {"name": "TechHost", "portrait": "assets/host.png",
           "voice_model": "de_DE-thorsten-high", "voice": "de+m3", "voice_pitch_semitones": 1.0,
           "piper_length_scale": 0.98}
},
"studios": {
  "classic": {"background": "assets/background.jpg", "desk_foreground": "assets/desk_foreground.png"},
  "tech": {"background": "assets/background.jpg",
           "scenes": {"intro_mode": "static", "intro_static_type": "color", "intro_static_color": "#0f3b2e"}}
},
"shows": [
  {"id": "main", "host_id": "newshost", "studio_id": "classic"},
  {"id": "technology", "host_id": "tech", "co_host_id": "newshost", "studio_id": "tech"}
]
```

Ein vollständiges Beispiel steht in `config.shows.example.json`.

## Felder

| Moderator (`hosts.<id>`) | Wirkung |
| --- | --- |
| `name`, `gender`, `portrait`, `lip_sync` | Aussehen im Video (`presenter_settings`) |
| `voice_model` | Piper-Stimme, z. B. `de_DE-thorsten-high`. Die Datei `models/<name>.onnx` (+ `.onnx.json`) muss vorhanden sein, sonst wird `de_DE-thorsten-high` verwendet und das im Log vermerkt. |
| `voice` | eSpeak-NG-Stimme für den Rückfall, z. B. `de`, `de+m3`, `de+f2` |
| `voice_pitch_semitones` | Tonhöhe −6 bis +6 Halbtöne, Sprechtempo bleibt gleich |
| `piper_length_scale` | Sprechtempo von Piper (größer = langsamer) |

| Studio (`studios.<id>`) | Wirkung |
| --- | --- |
| `background` | Studiobild |
| `desk_foreground` | Tisch im Vordergrund |
| `scenes` | Szeneneinstellungen (Intro-Art, Farben, Texte); werden mit den geerbten Szenen zusammengeführt |

IDs bestehen aus Kleinbuchstaben, Ziffern, `_` und `-`. Unbekannte Felder und unbekannte IDs werden beim Prüfen der Konfiguration abgelehnt.

## Reihenfolge

1. Grundeinstellungen der Konfiguration
2. Studio, dann Moderator
3. Felder, die die Show direkt setzt (`presenter`, `studio`, `presenter_settings`, `voice_pitch_semitones` …) – sie haben Vorrang

`produce_show.py` schreibt `host_id`, `co_host_id` und `studio_id` in `show.json`.

## Wechselmoderation (optional)

Mit `co_host_id` wechseln sich zwei Stimmen bei den Meldungen ab: Meldung 1, 3, 5 … spricht der Moderator (`host_id`), Meldung 2, 4 … der zweite Moderator. Begrüßung, Datum und Abschluss spricht der Moderator. Im Bild bleibt der Moderator; zwei Personen im Bild und Lippensynchronität für mehrere Moderatoren folgen mit den KI-Hosts (Epic E15).

## Zusätzliche Piper-Stimmen

Piper-Stimmen gibt es unter https://huggingface.co/rhasspy/piper-voices. Für `de_DE-kerstin-low`:

```sh
base=https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/kerstin/low
curl -fL "$base/de_DE-kerstin-low.onnx" -o models/de_DE-kerstin-low.onnx
curl -fL "$base/de_DE-kerstin-low.onnx.json" -o models/de_DE-kerstin-low.onnx.json
```

Die Lizenz der jeweiligen Stimme steht in ihrer Modellkarte. Die geplante Workflow-Sendung lädt nur `de_DE-thorsten-high`; Shows werden lokal mit `scripts/produce_show.py` erzeugt.
