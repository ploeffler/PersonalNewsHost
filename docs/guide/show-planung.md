# Planung und Laufzeitbudget

Dieses Dokument beschreibt, wann Sendungen und Shows laufen und wie viele GitHub-Actions-Minuten das pro Monat kostet. Die Zahlen erzeugt `python3 scripts/show_schedule.py budget`; Grundlage sind die Zeitpläne in `.github/workflows/`, der Sendeplan in `config.json` und gemessene Laufzeiten in `planning/workflow-minutes.json`.

## Freies Kontingent

- **Öffentliches Repository** (PersonalNewsHost ist öffentlich): Standard-Runner von GitHub sind kostenlos, es gibt kein Minutenlimit. Das freie Kontingent wird nicht berührt.
- **Privates Repository** (z. B. ein privater Fork) mit GitHub Free: 2000 Linux-Minuten pro Monat. GitHub rundet jeden Job auf volle Minuten auf.

## Verbrauch mit den Einstellungen dieses Branches

Messung vom 21.11.2026 (Laufhistorie `main` und dieses Branches), 30-Tage-Monat, Sendeplan aus `config.json` (alle 3 Stunden):

| Workflow | Auslöser (UTC) | Läufe/Monat | erwartet (min) | Obergrenze Timeouts (min) |
| --- | --- | ---: | ---: | ---: |
| `example-newsshow.yml` | `push/PR` | 4 | 24 | 80 |
| `fork-sync.yml` | `17 3 * * *` | 30 | 60 | 900 |
| `foundation-ci.yml` | `push/PR` | 100 | 300 | 1500 |
| `linux-install-smoke.yml` | `push/PR` | 35 | 70 | 525 |
| `news.yml` | `17 * * * *` | 720 | 1680 | 28800 |
| `short-updates.yml` | `7,22,37,52 * * * *` | 2880 | 5940 | 43200 |
| `task-sync.yml` | `push/PR` | 75 | 75 | 1500 |
| `wiki-sync.yml` | `push/PR` | 2 | 2 | 20 |
| **Summe** | | | **8151** | 76525 |

„Obergrenze Timeouts“ ist der theoretische Höchstwert, wenn jeder Lauf bis zu seinem `timeout-minutes` hängt. Die erwarteten Werte beruhen auf Laufzeiten vor den Einsparungen unten und sind daher eher zu hoch.

**Ergebnis:** Im öffentlichen Repository kostenlos. Für ein privates Repository reicht das Kontingent mit viertelstündlichen Kurzupdates nicht: 2880 Läufe brauchen allein schon mindestens 2880 Minuten, weil jeder Job mindestens eine Minute zählt.

## Privates Repository: Profil unter 2000 Minuten

| Teil | Einstellung | Minuten/Monat |
| --- | --- | ---: |
| Kurzupdates | `cron: '7,37 5-22 * * *'` (alle 30 min, 6–24 Uhr MEZ) | 1080 |
| Sendung | `cron: '5 5,10,18 * * *'` (7, 12, 20 Uhr MEZ; im Sommer eine Stunde später), etwa 5 min je Ausgabe | 450 |
| Fork-Abgleich | täglich, 2 Jobs | 60 |
| Prüfungen bei Pushes | etwa 100 Pushes | 300 |
| **Summe** | | **1890** |

Damit bleibt ein Puffer von gut 100 Minuten. Der Test `tests/test_show_schedule.py` rechnet dieses Profil nach.

## Einsparungen in den Workflows

- **`news.yml`** prüft den Sendeplan jetzt als ersten Schritt. Abhängigkeiten, Konfigurationsprüfung und die Testsuite laufen nur noch, wenn eine Ausgabe fällig ist. Bei stündlichem Auslöser und einer Ausgabe alle 3 Stunden stoppen zwei von drei Läufen nach wenigen Sekunden.
- **`short-updates.yml`** führt bei geplanten Läufen keine Tests mehr aus. Die Tests laufen bei jedem Push in `foundation-ci.yml` und bei manuellen Starts. Sprachausgabe und FFmpeg werden nur bei einer Eilmeldung installiert (T013).
- **Feeds nur einmal pro Lauf laden:** Eine Feed-Kopie, die jünger als `feed_resilience.reuse_seconds` (Standard 300 s) ist, wird ohne erneuten Download verwendet. So lädt der Kurzupdate-Lauf jeden Feed einmal statt zweimal (Eilmeldungsprüfung und Nachrichtenspeicher).
- **Caches:** Piper-Stimme, Ubuntu-Pakete und pip-Downloads (`news.yml`), letzte gültige Feeds (`.cache/feeds`, T071).
- **Concurrency:** Sendung und Kurzupdates teilen die Gruppe `personalnewshost-publish` und laufen nie gleichzeitig. `foundation-ci.yml` und `linux-install-smoke.yml` brechen ältere Läufe ab, sobald ein neuer Push kommt.
- **Timeouts:** Jeder regelmäßige Workflow hat `timeout-minutes` (Sendung 40, Kurzupdates 15, Prüfungen 15, Wiki 10). Ohne Angabe würde GitHub bis zu 360 Minuten warten.

## Shows planen

Shows aus `shows` werden lokal mit `scripts/produce_show.py` produziert und verbrauchen keine Actions-Minuten. Jede Show bekommt einen eigenen Cron-Auslöser aus ihrem `schedule` (`interval_hours`, `start_hour_local`, `days`, `timezone`):

```sh
python3 scripts/show_schedule.py crontab --config config.json > pnh-shows.cron
crontab pnh-shows.cron
```

Beispiel für zwei Shows:

```
CRON_TZ=Europe/Vienna
5 6,14,22 * * * cd /srv/pnh && mkdir -p .cache/locks && flock -n …/show-main.lock flock -w 3000 …/render.lock python3 scripts/produce_show.py --show main >> .cache/show-main.log 2>&1
CRON_TZ=Europe/Vienna
5 18 * * 1-5 cd /srv/pnh && … --show technology …
```

- `flock -n …/show-<id>.lock`: Läuft eine Show noch, fällt ihr nächster Start aus. Eine Show überholt sich nie selbst.
- `flock -w 3000 …/render.lock`: Alle Shows teilen sich eine Render-Sperre. Es rendert immer nur eine Show; die nächste wartet bis zu 50 Minuten.
- `CRON_TZ` setzt die Zeitzone der Show (cronie und Debian-cron unterstützen das).

Würde eine Show stattdessen auf GitHub produziert, kostet jede Ausgabe etwa 5 Minuten. `budget` zeigt diesen Wert pro Show, wenn die Konfiguration Shows enthält.

## Werte aktualisieren

1. Laufzeiten aus der Actions-Historie in `planning/workflow-minutes.json` eintragen (Minuten pro Lauf, Läufe pro Monat bei Push-Workflows).
2. `python3 scripts/show_schedule.py budget` ausführen und die Tabelle oben ersetzen. Der Test prüft, dass die Summe hier mit der Berechnung übereinstimmt.
3. Für ein privates Repository: `python3 scripts/show_schedule.py budget --private` meldet einen Fehler, wenn die erwartete Summe über 2000 Minuten liegt.
