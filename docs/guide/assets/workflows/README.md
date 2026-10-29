# Ablaufgrafiken

Die technischen Abläufe werden in Deutsch und Englisch als echte Bilder eingebettet. PNG dient der Anzeige in Dokumentation und Wiki, SVG ist die skalierbare Variante. Die bearbeitbaren Quellen liegen als `.dot` daneben.

Mit installiertem Graphviz aus dem Repositorywurzelverzeichnis neu erzeugen:

```bash
python3 scripts/render_workflow_diagrams.py
```

Der Wiki-Synchronisationsworkflow kopiert diese Dateien in das Wiki-Repository und verwendet für eingebettete Bilder dessen direkte Raw-URLs. So bleiben sie unabhängig vom Branch und von einer GitHub-Pages-Veröffentlichung erreichbar.
