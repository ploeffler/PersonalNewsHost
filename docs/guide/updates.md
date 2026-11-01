# Zusätzlicher Release-Versionscheck

Stand: 01.11.2026, frühere Release-Interpretation / Entwicklung 0.2.
Für den konkretisierten T195/T196-Auftrag siehe [täglicher Fork-/Branch-Abgleich](fork-sync.md).
Dieses Hilfsprogramm bleibt separat erhalten und ersetzt keine Ahead-/Behind-Prüfung aller Branches. **Prüfung implementiert, Installation
noch nicht implementiert.** Kein automatisches git pull, kein Imagewechsel und
keine Migration werden durch diese Befehle ausgeführt.

## Starten

```bash
python3 scripts/local_runtime.py check-updates
python3 scripts/local_runtime.py watch-updates
```

`check-updates` prüft, sobald das gespeicherte Intervall abgelaufen ist.
`watch-updates` prüft beim Start, soweit fällig, und danach automatisch weiter.
Es meldet nur neue Prüfversuche, keine identischen Statuszeilen im Minutentakt.
Stoppen mit Strg+C. Für eigene Parameter den direkten Einstieg verwenden:

```bash
python3 scripts/update_check.py --force
python3 scripts/update_check.py --watch --interval 86400
python3 scripts/update_check.py --watch --channel development
```

Standard: stabiler Kanal und 24 Stunden; Intervall 60 Sekunden bis 7 Tage.
`--force` umgeht beim ersten Versuch die gespeicherte Wartezeit. Bei API-Limits
nicht wiederholt erzwingen. Der Entwicklungskanal lässt auch Versions-Tags mit
Vorabkennung zu, verlangt aber ebenfalls einen bestätigten Release-Marker.
Bewegungen von main oder Full-featured-Newsoutlet sind keine verfügbaren Updates.

Ein dauerhaft startender systemd-/Containerdienst folgt mit dem Betriebsunterbau.
Jetzt muss der Watch-Prozess explizit gestartet werden; er wird nicht heimlich
installiert oder beim Rendern einer Sendung gestartet. Eine vorhandene private
Statusdatei wird nach Neustart weiterverwendet. Eine geänderte installierte
Identität oder ein Kanalwechsel erzwingt eine neue Prüfung statt alter Verfügbarkeit.

## Quelle und Freigabe

Originalquelle ist fest `ploeffler/PersonalNewsHost`; ein eigener Fork-origin wird
nicht als Original behandelt. Der Checker verwendet öffentliche GitHub-Anfragen
ohne Token und ohne Upload eigener Konfiguration, Secrets, Medien oder Prompts.
Die [Tags-API](https://docs.github.com/en/rest/repos/repos#list-repository-tags)
liefert Versions-Tags und Commitzuordnung. Tags werden numerisch/semantisch
sortiert: 0.10 folgt auf 0.9, Vorabversionen liegen vor der fertigen Version.

Ein Kandidat benötigt an seinem fixierten Commit den passenden bestätigten
`planning/documentation-release.json` mit completed/tests_passed=true und den
passenden Inhalt von VERSION. Separate GitHub-Releases werden zusätzlich auf
Entwurf/Vorabstatus geprüft. Ein bestätigter Versionstag ohne separates
Releaseobjekt bleibt gültig, wie das ursprüngliche v0.1. Die
[Release-API unterscheidet Releases von reinen Tags](https://docs.github.com/en/rest/releases/releases).

Bereits beobachtete Tag-Commit-Zuordnungen bleiben gespeichert. Eine spätere
Änderung ergibt `tag_changed`; auch ein verschobener installierter Tag wird bei
bekanntem installiertem Commit abgewiesen. Beim ersten Kontakt kann der Checker
keine frühere unbekannte Tagzuordnung rekonstruieren. Es ist keine kryptografische
Signaturprüfung und noch keine Bestätigung der Installationskompatibilität.

## Status und installierte Identität

`state/updates/check.json` enthält Originalquelle, Kanal, installierte Version,
Commit/Tag soweit bekannt, neueste bestätigte Version, Notizentext/-Link,
Zeitpunkte des letzten Versuchs und Erfolgs, nächsten Versuch und Fehlerklasse.
`update_available` ist nur bei erfolgreicher Prüfung und einer neueren Version
wahr. Bei Fehlern sind alte erfolgreiche Informationen noch sichtbar, aber nicht
als installierbares Update markiert. Kompatibilität lautet ausdrücklich
`requires_installation_preflight`; T196 muss sie vor Installation prüfen.

Ein Checkout liefert VERSION, HEAD, exakten Versionstag und einen booleschen
Hinweis auf lokale Änderungen. Ist HEAD keinem Versionstag zugeordnet, zeigt
das keinen offiziell installierten Release an. Ein laufender Entwicklungsstand
0.2 wird beispielsweise nicht auf den älteren Release 0.1 zurückgestuft.
Ohne Git stehen nur VERSION und entsprechend unvollständige Identität bereit.

Für spätere Containerbuilds kann `/app/build-info.json` diese Struktur bereitstellen:

```json
{
  "version": "0.1",
  "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "tag": "v0.1",
  "image_digest": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
}
```

Dies sind synthetische Platzhalter. Der Imagebuild muss echte Werte erzeugen;
dieser Checker ermittelt keinen Digest vom Dockerdaemon. Version muss zu VERSION
passen, Commit und Digest müssen gültige Formate haben. Der Manifestinhalt ist
lokale Buildmetadaten, keine unabhängig verifizierte Herkunftsbescheinigung.

## Offlinebetrieb und Grenzen

Netzwerkanfragen haben 10 Sekunden Timeout und 2 MB Antwortlimit. Discovery ist
auf fünf Tagseiten und zwanzig Releasekandidaten begrenzt; bei Überschreitung
wird ein Fehler gemeldet statt fälschlich „aktuell“. Sperrdatei und atomarer
privater Status verhindern konkurrierende Statusschreiber. Neue Statusdateien
haben Modus 0600. Private Zustandsverzeichnisse müssen vom Betreiber geschützt sein.

Fehler verändern keine Installation und keine Produktionsdatei. Wiederholungen
verwenden persistenten exponentiellen Backoff bis maximal 24 Stunden;
Rate-Limit-Header können die Wartezeit verlängern. Das öffentliche API-Limit ist
endlich; siehe [GitHub-Limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
Ungültiger lokaler Status oder unlesbare Pfade führen zu einer redigierten
CLI-Fehlermeldung, nicht zu einem Reset der gespeicherten Taghistorie.

Automatisches Einspielen, Datenmigration, Wartungsfenster, Produktionssperre und
Rollback sind **T196**, abhängig von Persistenz und Deployment. Kein positives
Prüfergebnis ermächtigt diesen Checker, lokale Codeänderungen zu überschreiben.
