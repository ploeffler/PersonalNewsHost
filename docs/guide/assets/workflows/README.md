# Ablaufgrafiken

Die technischen Abläufe werden in Deutsch und Englisch als echte Bilder eingebettet. PNG dient der Anzeige in Dokumentation und Wiki, SVG ist die skalierbare Variante. Die bearbeitbaren Quellen liegen als `.dot` daneben.

Grafiken und Wiki werden ausschließlich nach bestätigtem Abschluss einer Unterversion aktualisiert. Der Marker `planning/documentation-release.json` muss `completed: true`, `tests_passed: true` und die mit `VERSION` übereinstimmende Version enthalten. Danach den passenden Tag (z. B. `v0.1`) erzeugen. Normale Branch-Pushes lösen keine Dokumentationsveröffentlichung aus.

Mit installiertem Graphviz aus dem Repositorywurzelverzeichnis für die bestätigte Version erzeugen:

```bash
python3 scripts/render_workflow_diagrams.py --release-tag v0.1
```

Der Wiki-Synchronisationsworkflow kopiert diese Dateien in das Wiki-Repository und verwendet für eingebettete Bilder dessen direkte Raw-URLs. So bleiben sie unabhängig vom Branch und von einer GitHub-Pages-Veröffentlichung erreichbar.
