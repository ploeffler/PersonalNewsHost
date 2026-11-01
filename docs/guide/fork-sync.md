# Täglicher Abgleich und Synchronisierung aller Fork-Branches

Stand: 01.11.2026. T195/T196 auf dem Entwicklungsbranch. Diese Funktion vergleicht
Git-Branches eines Forks mit seinem Original; sie installiert keine Releases,
Container oder Modelle. Der frühere `update_check.py` prüft weiterhin ausschließlich
Release-Tags und erfüllt diesen Fork-Abgleich nicht.

## Einmalig im eigenen Fork einrichten

1. Diese Implementierung einschließlich `.github/workflows/fork-sync.yml`,
   `scripts/fork_check.py`, `scripts/fork_sync.py` und `scripts/update_check.py`
   muss im **Defaultbranch deines Forks** liegen. Der Zeitplan wird nicht aktiv,
   wenn die Dateien ausschließlich auf einem anderen Entwicklungsbranch liegen.
2. Im eigenen Fork **Actions aktivieren**. GitHub aktiviert geerbte Zeitpläne in
   neuen Forks nicht zwangsläufig; einmal prüfen und gegebenenfalls aktivieren.
3. Unter den Repository-Einstellungen **Issues einschalten**, falls deaktiviert.
   Für Hinweise den verwalteten Fork-Status-Issue abonnieren bzw. die gewünschten
   GitHub-Benachrichtigungen einstellen. Die Anwendung versendet keine eigenen Mails.
4. Workflow **Check and synchronize all fork branches** einmal manuell ohne
   Synchronisierung starten. Die Zusammenfassung muss alle Branches zeigen.
5. Danach ist täglich **03:17 UTC** eine automatische Prüfung vorgesehen.
   GitHub kann Zeitpläne verzögern oder bei Inaktivität deaktivieren; das ist kein
   minutengenauer oder dauerhaft garantierter Scheduler. Siehe
   [GitHub-Schedule-Regeln](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

Der Workflow arbeitet ausschließlich in Forks. Im Originalrepository wird er
übersprungen. Diese Entwicklung ändert den Defaultbranch des Originalrepositorys
nicht automatisch; der aktuelle Implementierungsstand muss erst dort bzw. im
Fork bewusst integriert werden. Ein Repositorywechsel oder ein neuer Fork
übernimmt keine Secrets und Variablen des alten Repositorys.

## Was wird verglichen?

Standardmäßig wird das von GitHub bestätigte Original (`source`) verwendet,
sonst der direkte Parent. Damit bleibt auch ein Fork eines Forks am Original.
Ein explizites `--upstream OWNER/REPO` muss Parent oder Source dieses Forks sein.
Für Forks von ploeffler/PersonalNewsHost ist das Original ploeffler/PersonalNewsHost. Es wird nicht nur der ausgecheckte/default Branch geprüft.

Alle Branchlisten werden vollständig paginiert gelesen. Gleichnamige Branches
werden anhand ihrer fixierten Commitköpfe verglichen; es ist kein Release-Tag nötig.
Die maximale Discovery umfasst 100 Seiten je Liste; Überschreitung ist ein Fehler,
keine Meldung „aktuell“. Eine Prüfung ist ein API-Snapshot, keine globale Sperre
beider Repositorys während anderer Benutzer neue Branches anlegen.

| Status | Bedeutung |
|---|---|
| current | keine eigenen und keine fehlenden Commits |
| ahead | eigene Commits, nichts aus dem Original fehlt |
| behind | Originalcommits fehlen, keine eigenen Commits |
| diverged | sowohl eigene als auch fehlende Commits |
| fork_only | eigener Branch ohne gleichnamigen Originalbranch; bleibt erhalten |
| upstream_only | Originalbranch fehlt im Fork; sichtbar und manuell anlegbar |
| unknown | Vergleich fehlgeschlagen, z. B. wegen Zugriffs-/API-Limitfehler |

### Selbst angelegte Arbeitsbranches mit anderem Namen

Wenn du im Fork z. B. `meine-sendung` angelegt hast und dieser dem Originalbranch
`Full-featured-Newsoutlet` folgen soll, lege im Fork eine Repository-Variable
`FORK_SYNC_BRANCH_MAP` mit diesem JSON-Wert an:

```json
{"meine-sendung": "Full-featured-Newsoutlet"}
```

Beide Workflowjobs verwenden dieselbe Zuordnung. Nicht aufgeführte Forkbranches
werden weiterhin mit ihrem gleichnamigen Originalbranch verglichen. Es wird
nicht geraten, auf welchem Originalbranch ein beliebiger Arbeitsbranch basiert.
Ein konfigurierter, aber fehlender Originalbranch ergibt `unknown`; ein fehlender
konfigurierter Forkbranch ergibt einen Konfigurationsfehler. Die Übernahme ändert
nur den Forkbranch und behält dessen Namen. Bei eigenen Commits gilt weiterhin
die ausdrückliche Mergeauswahl. Die Tabelle zeigt beide Branchnamen.

CLI-Alternative: `--branch-map-json '{"meine-sendung":"Full-featured-Newsoutlet"}'`
an `fork_check.py` oder `fork_sync.py` übergeben.

Für jeden gemeinsamen bzw. zugeordneten Branch gibt es Ahead-/Behind-Zahlen und einen Vergleichslink.
Der Issue enthält einen Snapshot des letzten geänderten Rückstands. Der verwaltete Issue ist zusätzlich mit `personalnewshost-fork-sync` markiert;
ein beliebiger fremder Issue-Text wird nicht als sein Status übernommen. Identische
Rückstände erzeugen weder neue Issues noch tägliche Kommentare. Bei einem neuen
oder veränderten Rückstand aktualisiert der Workflow denselben Issue und ergänzt
einen Kommentar. Sind alle Rückstände behoben, wird er mit Ergebnis geschlossen.
Die komplette aktuelle Liste steht weiterhin in der Actions-Zusammenfassung.

Ob du eine E-Mail oder einen GitHub-Hinweis erhältst, hängt von deinem Issue-
Abonnement und deinen GitHub-Einstellungen ab. Fehlende Issue-Rechte werden als
Workflowfehler gemeldet; sie werden nicht als erfolgreiche Benachrichtigung gewertet.

## Übernahme manuell auslösen

Unter Actions den Workflow starten und **synchronize** aktivieren.

- `branches`: je Zeile genau ein Branchname; Slashes sind erlaubt.
- Keine Auswahl: nur alle Branches mit Status `behind` übernehmen.
- `allow_merge`: nur für ausdrücklich ausgewählte divergente Branches aktivieren.

Bei `behind` wird mit `force=false` auf den festgestellten Originalcommit aktualisiert.
Bei `diverged` wird ohne ausdrückliche Mergeauswahl nichts geschrieben. Der bewusste
Merge erhält die eigenen Commits; ein Konflikt meldet `merge_conflict`, ohne Force-Push.
Vor jeder Änderung werden beide Branchköpfe erneut gelesen. Geänderte Köpfe führen
zu `heads_changed_retry_check`; einen neuen Check starten. Schreibaufrufe werden
nach Netzwerkfehlern nicht blind wiederholt, weil das Ergebnis unklar sein kann.
Der Branchstatus wird nach einem Versuch neu eingelesen.

Geschützte Branches werden nicht direkt verändert; der Bericht bietet einen Link
zum Vorbereiten eines Synchronisierungs-PRs. Dieser Link legt noch keinen PR an.
`fork_only` wird weder gelöscht noch umbenannt. `upstream_only` wird nicht ungefragt
angelegt. Unabhängige Ergebnisse werden je Branch ausgewiesen, nicht als pauschaler
Erfolg. Wiederholte Synchronisierung eines bereits aktuellen Branches ist harmlos.

## Automatische Übernahme einschalten

Im Fork unter **Settings → Secrets and variables → Actions → Variables** die
Repository-Variable `FORK_SYNC_AUTOMATIC` auf `true` setzen.

Damit folgt auf den täglichen Check eine automatische Übernahme aller reinen
`behind`-Branches. Divergente, geschützte und nicht vergleichbare Branches bleiben
zur Prüfung stehen. Für Abschalten die Variable entfernen oder auf `false` setzen.
Die Prüfung und Hinweise laufen weiter. Automatischer Modus ist standardmäßig aus;
die tägliche Prüfung bleibt nach einmaliger Actions-Einrichtung automatisch.

## Berechtigungen und lokale Arbeitskopie

Der Prüfjob benötigt Contents-Leserecht und Issues-Schreibrecht. Der getrennte
Synchronisierungsjob benötigt Contents- und Issues-Schreibrecht. Standard ist der
auf diese Jobberechtigungen beschränkte `GITHUB_TOKEN`. Es werden keine Git-
Checkout-Credentials gespeichert. HTTP-Redirects werden abgewiesen, damit ein
Authentifizierungsheader nicht auf einen anderen Host weitergereicht wird.

Für Änderungen an Workflowdateien oder abweichende Repositoryregeln kann der
Standardtoken nicht ausreichen. Falls nötig einen ausschließlich für diesen Fork
berechtigten Token mit den benötigten Contents-/Issues- und Workflowrechten als
**Actions Secret `FORK_SYNC_TOKEN`** hinterlegen. Nur der Synchronisierungsjob
verwendet dieses optionale Secret. Geschützte Branches bleiben trotzdem ausgenommen.
Keine Tokens in Git, Branch-Namen, CLI-Argumente, Logs oder Issues schreiben.

Es wird nur der Remote-Fork geändert. Lokale Dateien, uncommittete Änderungen und
eine laufende Installation werden nicht angefasst. Eine spätere lokale Übernahme
muss separat per Fetch und verlusterhaltendem Merge erfolgen. Synchronisierung
ist keine Aussage darüber, ob neue Originalcommits bereits deine Produktions-
oder Installationstests bestanden haben. Branchschutz und CI-Regeln weiterhin nutzen.

## CLI und Tests

Die Module benötigen nur Python-Standardbibliothek. Aus dem Repository:

```bash
python3 scripts/fork_check.py --fork DEIN-NAME/PersonalNewsHost
python3 scripts/fork_check.py --fork DEIN-NAME/PersonalNewsHost --notify
python3 scripts/fork_sync.py --fork DEIN-NAME/PersonalNewsHost --branch Full-featured-Newsoutlet
python3 scripts/fork_sync.py --fork DEIN-NAME/PersonalNewsHost --all-behind
python3 scripts/fork_sync.py --fork DEIN-NAME/PersonalNewsHost --branch EIGENER-BRANCH --merge
```

Die letzten drei Befehle schreiben bewusst in den Remote-Fork. Für CLI-Zugriff
wird `GITHUB_TOKEN` aus dem Prozesskontext gelesen; der Token wird nie ausgegeben.
Öffentliche Lesetests funktionieren ohne Token innerhalb der API-Limits. Vorübergehende
Lesefehler werden höchstens dreimal mit Backoff versucht. Nach erkanntem API-Limit
werden weitere Netzwerkaufrufe desselben Laufs bis zum Reset zurückgestellt;
schreibende Aufrufe werden nie blind wiederholt.
`--report PFAD` speichert optional einen privaten JSON-Bericht mit Modus 0600.
Es gibt keine automatische Codeänderung allein durch `fork_check.py` ohne `--notify`.
`--notify` schreibt ausschließlich den Hinweis-Issue, keine Branches.

Die automatisierten Tests simulieren APIs, Schreibfehler und Branchzustände.
Ein echter **lesender** Test gegen ploeffler/QSSTV-Experimental und seinen Parent
jbdubbs/QSSTV-Experimental wurde durchgeführt. Keine Live-Synchronisierung und
keine echte Issue-Nachricht wurden bei der Entwicklung ausgelöst. Ein auf GitHub
aktivierter täglicher Fork-Lauf benötigt die oben genannte einmalige Einrichtung.
