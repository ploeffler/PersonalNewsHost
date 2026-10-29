# Redaktionelle Langversion aus gespeicherten Meldungen

Der aktive Standardablauf ist: RSS erfassen → 24-Stunden-Speicher → Ereignisgruppen → gemeinsamer redaktioneller Text → Quellenprüfung → Auswahl → Sprache/Video → Veröffentlichung. Die Langversion liest keine rohen Feeds oder Artikeltexte nach der Freigabe nach. Bilder und Medienmetadaten werden weiterhin während der Videoaufbereitung beschafft.

## Redaktionelle Formulierung

Die Standardmethode `local_extractive_multi_source` arbeitet lokal und ohne kostenpflichtige Dienste. Sie verbindet vollständige, möglichst ergänzende Sätze aus mehreren gespeicherten Quellen. Wiederholungen und Werbeteaser werden ausgelassen; Die Quellenangabe steht einmal gesammelt am Ende der Meldung; jeder verwendete Herausgeber wird dort nur einmal genannt. Die Satzbelege im Prüfbericht bleiben einzeln zugeordnet. Die Zahl der Sätze richtet sich weiterhin nach `editorial.max_sentences`. Weitere Quellen einer Gruppe können berücksichtigt worden sein, ohne einen zusätzlichen Satz beizusteuern. Es handelt sich um quellengebundene, extraktive Bearbeitung, keine freie sprachmodellgestützte Umformulierung oder Übersetzung.

Gruppen werden konservativ aus ähnlichen Überschriften gebildet. Alle Mitglieder müssen zueinander passen; erkennbare unterschiedliche Ortsangaben verhindern die Zusammenlegung. Die Gruppierung ist eine lexikalische Heuristik und keine vollständige semantische Ereigniserkennung.

## Faktualitätsprüfung: definierter Prüfumfang

`verify()` prüft den fertig formulierten Text vor der Auswahl und erneut vor der Vertonung. Jeder Nachrichtensatz muss vollständig in den normalisierten gespeicherten Quellsätzen vorkommen, eine passende Quellen-ID haben und seinen Beleg erhalten. Auch die Überschrift muss aus einer Gruppenquelle stammen. Zusätzliche freie Behauptungen außerhalb der geprüften Sätze werden zurückgewiesen. Namen, Zahlen, Verneinungen und Unsicherheitsformulierungen können deshalb nicht unbelegt verändert werden. Erkennbare abweichende Angaben zu Toten/Verletzten sowie nahezu gleichlautende Aussagen mit abweichender Verneinung oder Unsicherheit führen zur Rückstellung. Bei reparierbaren Beleg-/Textfehlern gibt es einen begrenzten Korrekturlauf; ungelöste Fälle bleiben gesperrt.

Die Freigabe bedeutet **Quellentreue**, nicht unabhängig bestätigte Wahrheit. Der Prüfer kann Fehler in den Ursprungsquellen oder alle semantischen Widersprüche nicht erkennen. Quellenunabhängigkeit wird nicht aus verschiedenen Herausgeberdomains abgeleitet. `independent_fact_check` bleibt ausdrücklich `false`.

## Produktion und Fehlerfälle

Alle Gruppen werden vor Anwendung der Sendungsgrenze bearbeitet und geprüft. Erst danach werden aktuelle, freigegebene Gruppen mit Herausgebervielfalt ausgewählt. Standardmäßig sind es fünf. Der Nachrichtenspeicher darf höchstens 30 Minuten seit dem letzten Abruf alt sein; Meldungen selbst dürfen höchstens 24 Stunden alt sein. Fehlt ein aktueller Speicher oder gibt es keinen freigegebenen Text, endet die Produktion ohne rohe Ersatztexte. Die veröffentlichte vorherige Sendung bleibt bestehen.

Der Workflow erfasst RSS vor der Produktion und aktualisiert anschließend die Zuordnung zur fertigen Sendung ohne erneuten Nachrichtenabruf. Bei gemeinsam formulierten Beiträgen werden die beitragenden gespeicherten Meldungen mit derselben Beitragsnummer gekennzeichnet. Die bestehende Video-/Telegram-Produktion und die Aufbewahrung der zwei letzten Videos bleiben erhalten.

## Bericht

`docs/editorial-report.json` enthält Quellenschnappschuss, Gruppen, Entwurf, Satzbelege, Prüfergebnisse, Korrekturversuche und Auswahl. Die Seite `editorial-pipeline.html` zeigt den Bericht lesbar. Ein als `preview` markierter Bericht ist noch keine produzierte Sendung. Der Workflow bietet den Bericht auch bei einer fehlgeschlagenen Produktion als Actions-Artefakt an; fehlgeschlagene Versuche ersetzen nicht den veröffentlichten Bericht.

Die Konfiguration `editorial.pipeline.enabled` ist standardmäßig aktiv. Ein ausdrücklich deaktivierter Modus bleibt für bestehende Render-Fixtures/Legacy-Betrieb erhalten; er ist kein automatischer Rückfall bei Prüfproblemen.
