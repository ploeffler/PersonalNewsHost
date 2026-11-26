# Erinnerung – offene Punkte (Stand 26.11.2026)

Branch: `Full-featured-Newsoutlet` (Regeln: `AGENTS.md`, Board: `planning/task-board.json`, Client: `scripts/task_client.py`). Aktive Version: 0.2.

## Erledigt (Sitzung 22.–26.11.2026)
- T021 Startseite, T030 Archiv, T022 Rubriken-/Sendungsseiten, T031 Volltextsuche, T032 Sitemap/Metadaten, T050 KI-Kennzeichnung, T062 Bildrechte, T182 Dienstbetrieb (start/stop/status, systemd) – alle `done`.
- Alle Abnahmen liefen unter den eigenen Client-IDs `claude-cloud-author` / `claude-cloud-review` auf ausdrückliche Anweisung des Benutzers, nicht durch einen unabhängigen Dritten. Berechtigungsregel dafür: `.claude/settings.local.json` (lokal, nicht eingecheckt).

## Entscheidungen
- `media.license_policy` ist standardmäßig `strict`: Publisher-Bilder nur mit Freigabe (`media.licensed_sources`), sonst Commons (PD/CC0) oder erzeugte Tafel. Auf `record_only` stellen, um frühere Bildnutzung beizubehalten.
- Abrufzeit auf Artikelseiten = Zeit der Sendung (keine Zeit je Quelle in den Daten).

## Offen / zu prüfen
- **T182:** Autostart nach echtem Neustart mit systemd auf Ubuntu 24.04 ist nicht getestet (nur `systemd-analyze verify` und Prozesstests).
- **T050/T280:** KI-Kennzeichnung im Videobild (rechts unten) fehlt noch; kommt mit T280.
- **T062:** Abspann-Zeile „Bilder: …" nur im Render-Lauf, nicht visuell geprüft.
- **Abnahmen:** Alle oben genannten Aufgaben sind nur selbst abgenommen; unabhängige Prüfung wäre sinnvoll.

## Nächste Aufgaben (0.2, frei)
- T183 Docker-Image und Compose-Betrieb (danach T184, T185, T186, T188 …).
- T124 Bild- und Medienherkunft prüfen.
