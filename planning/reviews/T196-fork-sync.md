# T196: Verlustfreie Remote-Forksynchronisierung

Explizit ausgewählte Branches oder automatisch nur reine behind-Branches werden
aktualisiert. Fast-forward ausschließlich force=false; eigene Commits bleiben
über explizite Mergeauswahl erhalten. Konflikte, Kopfbewegungen, Branchschutz,
fehlende Rechte und unklare Netzwerkergebnisse werden einzeln ausgewiesen. Kein
blindes Wiederholen schreibender API-Aufrufe. Vergleich danach neu eingelesen.
PR-Link ist ein Angebot, kein ungefragt erzeugter PR. Eigene/fehlende Branches
werden weder gelöscht noch automatisch angelegt. Lokale Checkouts bleiben unberührt.

Workflow täglich 03:17 UTC, nur in Forks und mit Concurrency-Sperre. Prüfjob hat
keine Contents-Schreibrechte; gesonderter Schreibjob nur bei manuellem Start oder
FORK_SYNC_AUTOMATIC=true. Alle Aktionen versioniert gepinnt. Standardtoken oder
bewusst eingerichtetes Fork-Secret; Workflowänderungen können zusätzliche Rechte
benötigen. Keine echten Branchupdates oder Issue-Nachrichten bei Entwicklung.

Automatische Tests decken Requests, Fehlerfälle und Nichtüberschreiben eigener
History ab; tatsächliche GitHub-Schreiboperationen werden simuliert. Gesamtergebnis
im Review. Tag v0.1 und main des Originalrepositorys bleiben unverändert. Aktiver
Tagesbetrieb erfordert einmalige Einrichtung im Fork-Defaultbranch. Kein Release.
