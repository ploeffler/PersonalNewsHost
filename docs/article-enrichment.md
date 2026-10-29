# Artikeltexte vor der Redaktion ergänzen

`collect_news.py` speichert weiterhin den originalen RSS-Text als `rss_text`. Reicht dieser als Nachrichtentext aus, bleibt er die bevorzugte Quelle. Bei leerem oder sehr kurzem Text folgt der Sammler dem Artikellink, bevor Ereignisse gruppiert, formuliert und auf Quellenbelege geprüft werden.

Die Extraktion berücksichtigt ORF-Artikelbereiche, strukturierte JSON-LD-Artikeltexte und Artikelabsätze. Wenn installiert, dient `rdrr` als letzte Rückfallebene. Seitentitel und Feedüberschrift müssen zusammenpassen. Navigation, Einwilligungsseiten und erkennbare Bezahlschranken werden nicht als Nachrichtentext übernommen. Weiterleitungen bleiben auf derselben Website; öffentliche HTTP(S)-Adressen, Zeit- und Größenlimits begrenzen den Abruf.

In `config.json`, `config.example.json` und `docs/config.json`:

```json
"article_enrichment": {
  "enabled": true,
  "max_fetches_per_run": 24
}
```

Pro Sammlerlauf werden höchstens 24 ergänzende Artikel abgerufen; der konfigurierbare Wert ist auf 60 begrenzt. Leere Beschreibungen und ORF-Links haben Vorrang. Zurückgestellte Abrufe werden im nächsten Lauf erneut berücksichtigt. Erfolgreiche Texte werden sechs Stunden zwischengespeichert; Änderungen an Überschrift, Feedtext oder Feed-Revisionsdatum verwerfen den bisherigen Cache. Fehler werden nach 30 Minuten erneut versucht, Einwilligungs-/Bezahlschranken nach sechs Stunden. Ein fehlgeschlagener erneuter Abruf behält einen passenden älteren Schnappschuss samt ursprünglicher Abrufzeit.

Der Nachrichtenspeicher enthält `text_origin`, `article_text` und `article_fetch` mit Abrufstatus, Original-/Zieladresse, Extraktionsmethode, Zeit und SHA-256 des übernommenen Textes. Ursprüngliche Veröffentlichungs- und Erstfundzeiten bleiben erhalten. Der lesbare Redaktionsbericht zeigt diese Herkunft bei den Satzbelegen. Sudoku- und datierte Kreuzworträtsel-Einträge werden separat als Nicht-Nachrichten aufgeführt.

Die ergänzten Texte durchlaufen dieselbe redaktionelle Quellenprüfung. Diese prüft die Deckung durch gespeicherte Quellen und ist keine unabhängige Bestätigung der berichteten Tatsachen. Nicht zugängliche oder unpassende Artikel bleiben ohne erfundenen Ersatztext zurückgestellt.

Tests: `test_article_enrichment.py`, `test_collect_news.py`, `test_editorial_pipeline.py` und `test_editorial_report_browser.cjs`.
