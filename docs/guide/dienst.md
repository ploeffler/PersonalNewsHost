# Dienstbetrieb unter Linux (Scheduler und lokale Auslieferung)

`scripts/service.py` ist ein Dauerdienst: Er prüft regelmäßig, ob eine Sendung fällig ist (Zeitplan aus `automation`, wie `local_runtime.py due`), startet fällige Produktionsläufe als eigene Kindprozesse und liefert `out/public` lokal aus (`127.0.0.1`, Standardport 8080). Voraussetzung ist die Installation nach [Linux-Installation](linux-installation.md).

## Skripte

```bash
./start.sh     # startet im Hintergrund; ein zweiter Aufruf meldet „läuft bereits"
./status.sh    # JSON-Bericht; Exitcode 0 = läuft, 3 = läuft nicht
./stop.sh      # beendet den Dienst; ohne laufenden Dienst ein sicherer No-op
```

Einstellungen über Umgebungsvariablen: `PNH_PORT` (Standard 8080), `PNH_TICK_SECONDS` (Prüfintervall, 5–3600, Standard 60). Logdatei: `state/service/service.log`; Zustand: `state/service/state.json`.

## Garantien

* **Genau eine Instanz:** exklusive Sperre `state/service/service.lock`. Sie endet mit dem Prozess, es bleibt keine veraltete Sperre zurück.
* **Nur eigene Prozesse:** `stop.sh` signalisiert nur den geprüften Dienstprozess (gleicher Benutzer, Projektordner in der Befehlszeile). Hält ein fremder Prozess die Sperre, wird nichts beendet.
* **Geordnetes Beenden:** Der Dienst stoppt den Scheduler und die Auslieferung und wartet bis 90 s auf laufende Produktionsläufe. Danach werden sie samt eigener Prozessgruppe beendet (SIGTERM, nach 10 s SIGKILL) und als `interrupted` im Zustand vermerkt.
* **Wiederaufnahme ohne Doppelsendung:** Der Zustand merkt sich je Sendung den zuletzt produzierten Slot. Nach einem Neustart wird nur produziert, wenn ein Slot fällig und noch nicht produziert ist; ein unterbrochener Lauf wird dann wiederholt. Ein fehlgeschlagener Lauf wird beim nächsten Prüfintervall erneut versucht.
* **Überwachung:** `status.sh` zeigt Scheduler (`ok`/`error`), HTTP-Status, laufende Aufträge, letzte Produktion, unterbrochene Aufträge und Fehler. Fehlt `out/public`, ist die Auslieferung `unavailable` und wird bei jedem Intervall neu versucht.

## Autostart mit systemd (optional)

```bash
python3 scripts/service.py install-systemd     # schreibt ~/.config/systemd/user/personalnewshost.service
systemctl --user daemon-reload
systemctl --user enable --now personalnewshost.service
loginctl enable-linger "$USER"                 # einmalig: Start nach Neustart auch ohne Anmeldung
```

Die Unit verwendet `run --managed systemd`. Läuft der Dienst unter systemd, verweisen `start.sh` und `stop.sh` auf `systemctl --user start|stop personalnewshost.service` und ändern nichts. Entfernen: `python3 scripts/service.py uninstall-systemd`, danach `systemctl --user disable --now personalnewshost.service`. Eine abweichende vorhandene Unit wird nur mit `--force` überschrieben. Es wird kein sudo verwendet.

Geprüft ist die Syntax der Unit mit `systemd-analyze verify` und der Ablauf start/status/stop/erneuter Start mit echten Prozessen. Ein Test des Autostarts nach einem echten Neustart auf Ubuntu 24.04 steht noch aus.
