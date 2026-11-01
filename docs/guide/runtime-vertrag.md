# Gemeinsamer Betriebsvertrag für Linux und Container

Stand: 01.11.2026, T180 / Entwicklung 0.2. Derselbe Einstieg gilt im Checkout und
in einem künftigen Containerimage: `python3 scripts/local_runtime.py BEFEHL`.
Ein Dockerimage oder Linux-Dienst wird damit noch nicht mitgeliefert.

## Pfade und Persistenz

Alle Standardpfade beziehen sich auf den Quellcode-Hauptordner, unabhängig vom
aktuellen Arbeitsverzeichnis. Im Container ist dafür `/app` vorgesehen.

| Zweck | Checkout-relativer Pfad | Containerziel | Behandlung |
|---|---|---|---|
| Konfiguration | config.json | /app/config.json | schreibgeschützter Mount, keine Secrets |
| Modellgewichte | models/ | /app/models/ | persistenter Mount; Laufzeit benötigt Leserechte |
| Host-/Studioassets | assets/ | /app/assets/ | bewusst bereitgestellte Medien |
| Privater Zustand | state/ | /app/state/ | persistentes privates Volume |
| Providercache/Ledger/Audit | state/providers/ | /app/state/providers/ | niemals öffentlich ausliefern |
| Interne Produktionen | out/productions/SHOW/ | /app/out/productions/SHOW/ | getrennt von öffentlicher Vorschau |
| Freigegebene Vorschau | out/public/ | /app/out/public/ | nur bewusst ausgewählte öffentliche Dateien |
| Geplantes Pflichtarchiv | archive/ | /app/archive/ | reserviert, Umsetzung mit T260 |

Der Einstieg liest Konfiguration optional über `--config /pfad/config.json`.
Das verschiebt weder Modelle noch Zustand: Der bisherige Generator verwendet
weiterhin die obigen Quellcode-relativen Verzeichnisse. Container müssen diese
Ziele mounten; beliebige externe Datenverzeichnisse werden noch nicht automatisch
umgeleitet. Der spätere Installer darf vorhandene Dateien nicht überschreiben.
Secrets werden nur im Dienstkontext bereitgestellt; dieser Einstieg liest oder
exportiert keine API-Schlüssel. Ein allgemeiner Secretdatei-Loader folgt später.

## Befehle

```bash
python3 scripts/local_runtime.py inspect
python3 scripts/local_runtime.py due --config config.json --show main
python3 scripts/local_runtime.py produce --config config.json --show main
```

`inspect` zeigt Pfade, Vorschauadresse und Publikationsstatus, ohne Konfiguration
oder Secrets zu lesen. `due` prüft nur den Termin und erzeugt keine Sendung.
Es verwendet `automation` der aufgelösten Show und deren Zeitzone (sonst UTC),
die bestehenden Sommerzeitregeln und das zuletzt erzeugte Show-Feeddatum.
GitHub-Eventvariablen überschreiben diesen lokalen Check nicht. Ein fehlender
Feed bedeutet noch keinen erfolgreichen Lauf; Fehler markieren nichts als erledigt.

`produce` startet bewusst eine Show über den vorhandenen isolierten Producer.
Konfiguration wird vor Produktion validiert. Ergebnisse landen intern unter
`out/productions/SHOW/`; es gibt keinen Telegramaufruf und keinen automatischen
Kopiervorgang in die öffentliche Vorschau. Ohne eigene Shows heißt die alte
Standardkonfiguration `main`. Die Produktion kann öffentliche Feeds und Medien
abrufen; „lokal“ bedeutet nicht zwangsläufig „ohne Internet“.

Der Scheduler-Prozesseinstieg ist ein einzelner Fälligkeitscheck. Dauerbetrieb,
prozessübergreifende Produktionssperren, Wiederaufnahme und systemd-Timer folgen
mit T070/T071/T182. Ein Shell-Timer darf `due` nicht als ausgereiften
Mehrshow-Scheduler missverstehen. Abhängigkeitsinstallation gehört zu T181.

## Öffentliche Ausgabe: lokale Vorschau

```bash
mkdir -p out/public
python3 scripts/local_runtime.py serve-preview --port 8080
```

Der Befehl liefert ausschließlich `out/public` auf `127.0.0.1:8080` aus.
Interne Produktionen werden nicht automatisch veröffentlicht. Symlinks im
Vorschauordner werden vor dem Start abgelehnt. Der Ordner muss während des
Betriebs vom vertrauenswürdigen Betreiber kontrolliert bleiben; dies ist kein
gehärteter Mehrbenutzer-Dateiserver. Stoppen mit Strg+C.

Diese HTTP-Vorschau ist kein öffentlicher Betriebslistener. Sie enthält keine
Admin-API oder Anmeldeseite. Für den späteren Betrieb gelten HTTPS 443 für die
öffentliche Ausgabe und HTTPS 8444 für die Administration (T191/T192). Es gibt
keinen automatischen unverschlüsselten Ersatz für fehlgeschlagenes TLS. Ein
Container-Loopback ist nur im Container erreichbar; jetzt keine öffentliche
Portfreigabe auf diesen Vorschauserver konfigurieren.

## Standardprofil und Abnahmegrenzen

Der Kern benötigt kein GitHub-Konto, Actions-Event oder GitHub-Secret.
Installierte Python-/FFmpeg-/Sprachabhängigkeiten und passende Medien bleiben
notwendig. Reale Provideradapter sind nicht enthalten; neue Installationen
aktivieren keine Cloudanbieter. Für funktionierende lokale Sprachausgabe und
bewusste eSpeak-Fallbackwahl siehe [Provider einrichten](provider-einrichtung.md).
GPU-Runtimes und T900 bleiben getrennte experimentelle Umgebungen.

Der Vertrag ist in beiden Betriebswegen identisch; reale Installation auf frischem
Linux und im Container wird erst mit T181/T183 geprüft. T180 bestätigt keine
funktionierende Containerbereitstellung, keine Archivgarantie und keinen sicheren
öffentlichen HTTPS-Betrieb. Ausgaben dieses Einstiegs werden nicht als
Veröffentlichungsfreigabe interpretiert.
