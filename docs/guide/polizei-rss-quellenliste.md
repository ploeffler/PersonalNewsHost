# Polizei, Feuerwehr, Rettungsdienst und Warnquellen: DE / AT

**Erweiterter Katalog:** 468 RSS-/Atom-Feeds, davon 218 zusätzlich aus Feuerwehr, Rettungsdienst, Katastrophenschutz und Warnsystemen. 31 weitere Web-/API-Quellen sind separat dokumentiert. Siehe die [Erweiterung am Ende](#erweiterung-feuerwehr-rettungsdienst-und-warnungen).

Stand: **2026-10-28**. Direkter Abruf und XML-Prüfung, keine Aktivierung in der Sendung.

**250 Polizeifeeds**, davon **198 mit Meldungen innerhalb von 14 Tagen**, 52 zur Aktualitätsprüfung. Zusätzlich 16 gemischte Blaulicht-Sammelfeeds und 2 verwandte österreichische Behördenfeeds. Atom-Darstellungen werden als Alternative vermerkt und nicht doppelt gezählt.

**Dateien:** [JSON-Katalog](../police-feed-catalog.json) · [OPML-Import](../police-feed-catalog.opml) · [Prüfprotokoll](../../research/police-rss/checks.json). Die OPML enthält aktuelle bestätigte Nachrichtenfeeds sowie technisch verfügbare Warnfeeds, nach Kategorien gruppiert. Gemischte Blaulicht-Sammelfeeds bleiben gesondert. Leere Warnfeeds können regulär sein. Web-/API-Quellen ohne Feed werden nicht importiert.

## Österreich: alle neun Landespolizeidirektionen

Das [offizielle BMI-Verzeichnis](https://www.bmi.gv.at/rss_feed/start.html) stellt die neun Landespolizeidirektionen jeweils als RSS und Atom bereit. Die zugehörigen RSS- und Atom-Adressen wurden geprüft; nur erfolgreich geladene RSS-Feeds werden unten ausgegeben.

| Bundesland | RSS | Atom |
|---|---|---|
| Burgenland | [RSS](https://www.bmi.gv.at/rss/bgld_presse.xml) | [Atom](https://www.bmi.gv.at/rss/bgld_pressea.xml) |
| Kärnten | [RSS](https://www.bmi.gv.at/rss/ktn_presse.xml) | [Atom](https://www.bmi.gv.at/rss/ktn_pressea.xml) |
| Niederösterreich | [RSS](https://www.bmi.gv.at/rss/noe_presse.xml) | [Atom](https://www.bmi.gv.at/rss/noe_pressea.xml) |
| Oberösterreich | [RSS](https://www.bmi.gv.at/rss/ooe_presse.xml) | [Atom](https://www.bmi.gv.at/rss/ooe_pressea.xml) |
| Salzburg | [RSS](https://www.bmi.gv.at/rss/sbg_presse.xml) | [Atom](https://www.bmi.gv.at/rss/sbg_pressea.xml) |
| Steiermark | [RSS](https://www.bmi.gv.at/rss/stmk_presse.xml) | [Atom](https://www.bmi.gv.at/rss/stmk_pressea.xml) |
| Tirol | [RSS](https://www.bmi.gv.at/rss/tirol_presse.xml) | [Atom](https://www.bmi.gv.at/rss/tirol_pressea.xml) |
| Vorarlberg | [RSS](https://www.bmi.gv.at/rss/vbg_presse.xml) | [Atom](https://www.bmi.gv.at/rss/vbg_pressea.xml) |
| Wien | [RSS](https://www.bmi.gv.at/rss/wien_presse.xml) | [Atom](https://www.bmi.gv.at/rss/wien_pressea.xml) |

Für die Sendung: LPD-Feeds können Meldungen ohne direkte Artikel-Links enthalten. In diesen Fällen ist `description` beziehungsweise Atom-`summary` die Textquelle. Die tatsächlich geprüfte Zahl vorhandener Artikel-Links, Textlängen und Meldungsdaten sind im JSON festgehalten.

Weitere österreichische Quellen:
- [Aktuelles aus dem Bundeskriminalamt](https://www.bmi.gv.at/rss/bk_presse.xml) (Polizeiliche Bundesbehörde).
- [Aktuelles aus dem BAK](https://www.bmi.gv.at/rss/bak_presse.xml) (verwandte Behörde, gesondert geführt).
- [Aktuelles aus dem BMI](https://www.bmi.gv.at/rss/bmi_presse.xml) (verwandte Behörde, gesondert geführt).

## Deutschland: direkte Behördenfeeds

| Behörde / Region | RSS | Aktualität |
|---|---|---|
| Pressemeldungen Polizei Bayern / Bayern | [Feed](https://www.polizei.bayern.de/rss_aktuelle_mitteilungen.xml) | aktuell |
| Aktuelle Polizeimeldungen / Berlin | [Feed](https://www.berlin.de/polizei/polizeimeldungen/index.php/rss) | aktuell |
| Internetwache Brandenburg - Pressemeldungen / Brandenburg | [Feed](https://polizei.brandenburg.de/pressemeldungen/rss) | aktuell |
| Alle Pressemitteilungen / Hessen | [Feed](https://www.polizei.hessen.de/presse-feed/all) | Prüfung nötig |

[Polizei Bayern](https://www.polizei.bayern.de/aktuelles/001127/index.html), [Polizei Brandenburg](https://polizei.brandenburg.de/liste/die-neuesten-polizeimeldungen-auf-dem-sc/60761) und [Polizei Hessen](https://www.polizei.hessen.de/Startseite/) dokumentieren eigene RSS-Angebote. Ob ein auswertbares Meldungsdatum vorliegt, steht pro Feed im Katalog. Undatierte Nachrichtenfeeds werden zur Prüfung markiert.

## Deutschland: einzelne Polizeibehörden über Presseportal

Ausgangspunkt ist das [Dienststellenverzeichnis](https://www.presseportal.de/blaulicht/dienststellen). Die Originalmitteilungen stammen von den jeweils genannten Behörden; technisch werden diese Feeds vom Presseportal ausgeliefert. Feuerwehr- und Rettungsdienst-Feeds sind in den zusätzlichen Kategorien am Ende dieser Liste enthalten; Zoll-, Gewerkschafts- und sonstige fachfremde Feeds bleiben ausgeschlossen. Überschneidungen mit Behörden-Webseiten sind möglich.

| Bundesland / Einordnung | Polizeifeeds | Davon aktuell |
|---|---:|---:|
| Baden-Württemberg | 23 | 21 |
| Bayern | 3 | 3 |
| Berlin/Brandenburg | 2 | 2 |
| Bremen | 3 | 2 |
| Bundesbehörden | 2 | 1 |
| Hamburg | 3 | 2 |
| Hessen | 29 | 16 |
| Mecklenburg-Vorpommern | 17 | 6 |
| Niedersachsen | 45 | 35 |
| Nordrhein-Westfalen | 51 | 49 |
| Rheinland-Pfalz | 39 | 33 |
| Saarland | 14 | 12 |
| Sachsen | 5 | 3 |

| Einordnung | Behörde / Absender | RSS | Aktualität |
|---|---|---|---|
| Baden-Württemberg | Bundespolizeidirektion Stuttgart | [Feed](https://www.presseportal.de/rss/dienststelle_74709.rss2) | prüfen: 2026-10-13 |
| Baden-Württemberg | Bundespolizeiinspektion Flughafen Stuttgart | [Feed](https://www.presseportal.de/rss/dienststelle_116095.rss2) | prüfen: 2026-10-05 |
| Baden-Württemberg | Bundespolizeiinspektion Karlsruhe | [Feed](https://www.presseportal.de/rss/dienststelle_116093.rss2) | aktuell |
| Baden-Württemberg | Bundespolizeiinspektion Konstanz | [Feed](https://www.presseportal.de/rss/dienststelle_116092.rss2) | aktuell |
| Baden-Württemberg | Bundespolizeiinspektion Offenburg | [Feed](https://www.presseportal.de/rss/dienststelle_75292.rss2) | aktuell |
| Baden-Württemberg | Bundespolizeiinspektion Stuttgart | [Feed](https://www.presseportal.de/rss/dienststelle_116091.rss2) | aktuell |
| Baden-Württemberg | Bundespolizeiinspektion Weil am Rhein | [Feed](https://www.presseportal.de/rss/dienststelle_116094.rss2) | aktuell |
| Baden-Württemberg | Hochschule für Polizei Baden-Württemberg | [Feed](https://www.presseportal.de/rss/dienststelle_110984.rss2) | aktuell |
| Baden-Württemberg | Landeskriminalamt Baden-Württemberg | [Feed](https://www.presseportal.de/rss/dienststelle_110980.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Aalen | [Feed](https://www.presseportal.de/rss/dienststelle_110969.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Einsatz | [Feed](https://www.presseportal.de/rss/dienststelle_110981.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Freiburg | [Feed](https://www.presseportal.de/rss/dienststelle_110970.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Heilbronn | [Feed](https://www.presseportal.de/rss/dienststelle_110971.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Karlsruhe | [Feed](https://www.presseportal.de/rss/dienststelle_110972.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Konstanz | [Feed](https://www.presseportal.de/rss/dienststelle_110973.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Ludwigsburg | [Feed](https://www.presseportal.de/rss/dienststelle_110974.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Mannheim | [Feed](https://www.presseportal.de/rss/dienststelle_14915.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Offenburg | [Feed](https://www.presseportal.de/rss/dienststelle_110975.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Pforzheim | [Feed](https://www.presseportal.de/rss/dienststelle_137462.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Ravensburg | [Feed](https://www.presseportal.de/rss/dienststelle_138081.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Reutlingen | [Feed](https://www.presseportal.de/rss/dienststelle_110976.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Stuttgart | [Feed](https://www.presseportal.de/rss/dienststelle_110977.rss2) | aktuell |
| Baden-Württemberg | Polizeipräsidium Ulm | [Feed](https://www.presseportal.de/rss/dienststelle_110979.rss2) | aktuell |
| Bayern | Bundespolizeidirektion München | [Feed](https://www.presseportal.de/rss/dienststelle_64017.rss2) | aktuell |
| Bayern | Polizeipräsidium Mittelfranken | [Feed](https://www.presseportal.de/rss/dienststelle_6013.rss2) | aktuell |
| Bayern | Polizeipräsidium Schwaben Nord | [Feed](https://www.presseportal.de/rss/dienststelle_169620.rss2) | aktuell |
| Berlin/Brandenburg | Bundespolizeidirektion 11 | [Feed](https://www.presseportal.de/rss/dienststelle_130761.rss2) | aktuell |
| Berlin/Brandenburg | Bundespolizeidirektion Berlin | [Feed](https://www.presseportal.de/rss/dienststelle_70238.rss2) | aktuell |
| Bremen | Bundespolizeiinspektion Bremen | [Feed](https://www.presseportal.de/rss/dienststelle_70255.rss2) | prüfen: 2026-10-12 |
| Bremen | Polizei Bremen | [Feed](https://www.presseportal.de/rss/dienststelle_35235.rss2) | aktuell |
| Bremen | Polizei Bremerhaven | [Feed](https://www.presseportal.de/rss/dienststelle_134196.rss2) | aktuell |
| Bundesbehörden | Bundeskriminalamt | [Feed](https://www.presseportal.de/rss/dienststelle_7.rss2) | aktuell |
| Bundesbehörden | Bundespolizeipräsidium | [Feed](https://www.presseportal.de/rss/dienststelle_73990.rss2) | prüfen: 2026-10-05 |
| Hamburg | Bundespolizeiinspektion Flughafen Hamburg | [Feed](https://www.presseportal.de/rss/dienststelle_70277.rss2) | prüfen: 2026-10-09 |
| Hamburg | Bundespolizeiinspektion Hamburg | [Feed](https://www.presseportal.de/rss/dienststelle_70254.rss2) | aktuell |
| Hamburg | Polizei Hamburg | [Feed](https://www.presseportal.de/rss/dienststelle_6337.rss2) | aktuell |
| Hessen | Bundespolizeidirektion Flughafen Frankfurt am Main | [Feed](https://www.presseportal.de/rss/dienststelle_74262.rss2) | aktuell |
| Hessen | Bundespolizeiinspektion Frankfurt/Main | [Feed](https://www.presseportal.de/rss/dienststelle_63987.rss2) | prüfen: 2026-09-09 |
| Hessen | Bundespolizeiinspektion Kassel | [Feed](https://www.presseportal.de/rss/dienststelle_63990.rss2) | aktuell |
| Hessen | Bundespolizeiinspektion Kriminalitätsbekämpfung Frankfurt | [Feed](https://www.presseportal.de/rss/dienststelle_177765.rss2) | prüfen: 2026-04-28 |
| Hessen | Hessisches Landeskriminalamt | [Feed](https://www.presseportal.de/rss/dienststelle_43563.rss2) | aktuell |
| Hessen | Hessisches Polizeipräsidium Einsatz | [Feed](https://www.presseportal.de/rss/dienststelle_43615.rss2) | prüfen: 2026-10-07 |
| Hessen | PASt (KvD) - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_62288.rss2) | prüfen: 2026-10-06 |
| Hessen | PD Hochtaunus - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_50152.rss2) | aktuell |
| Hessen | PD Limburg-Weilburg - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_50153.rss2) | aktuell |
| Hessen | PD Main-Taunus - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_50154.rss2) | aktuell |
| Hessen | PD Rheingau-Taunus - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_47764.rss2) | aktuell |
| Hessen | Polizei Eschwege | [Feed](https://www.presseportal.de/rss/dienststelle_44151.rss2) | prüfen: 2026-09-01 |
| Hessen | Polizei Homberg | [Feed](https://www.presseportal.de/rss/dienststelle_44149.rss2) | prüfen: 2026-09-01 |
| Hessen | Polizei Korbach | [Feed](https://www.presseportal.de/rss/dienststelle_44150.rss2) | prüfen: 2026-09-01 |
| Hessen | Polizei Presse A 49 | [Feed](https://www.presseportal.de/rss/dienststelle_148303.rss2) | prüfen: 2021-11-02 |
| Hessen | Polizeipräsidium Frankfurt am Main | [Feed](https://www.presseportal.de/rss/dienststelle_4970.rss2) | aktuell |
| Hessen | Polizeipräsidium Mittelhessen - Führungs- und Lagedienst | [Feed](https://www.presseportal.de/rss/dienststelle_17277.rss2) | aktuell |
| Hessen | Polizeipräsidium Mittelhessen - Pressestelle | [Feed](https://www.presseportal.de/rss/dienststelle_154582.rss2) | aktuell |
| Hessen | Polizeipräsidium Mittelhessen - Pressestelle Gießen | [Feed](https://www.presseportal.de/rss/dienststelle_43559.rss2) | prüfen: 2025-10-20 |
| Hessen | Polizeipräsidium Mittelhessen - Pressestelle Lahn - Dill | [Feed](https://www.presseportal.de/rss/dienststelle_56920.rss2) | prüfen: 2025-06-30 |
| Hessen | Polizeipräsidium Mittelhessen - Pressestelle Marburg-Biedenkopf | [Feed](https://www.presseportal.de/rss/dienststelle_43648.rss2) | prüfen: 2025-06-30 |
| Hessen | Polizeipräsidium Mittelhessen - Pressestelle Wetterau | [Feed](https://www.presseportal.de/rss/dienststelle_43647.rss2) | prüfen: 2025-06-30 |
| Hessen | Polizeipräsidium Nordhessen | [Feed](https://www.presseportal.de/rss/dienststelle_44143.rss2) | aktuell |
| Hessen | Polizeipräsidium Osthessen | [Feed](https://www.presseportal.de/rss/dienststelle_43558.rss2) | aktuell |
| Hessen | Polizeipräsidium Südhessen | [Feed](https://www.presseportal.de/rss/dienststelle_4969.rss2) | aktuell |
| Hessen | Polizeipräsidium Südosthessen | [Feed](https://www.presseportal.de/rss/dienststelle_43561.rss2) | aktuell |
| Hessen | Wiesbaden (KvD) - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_11815.rss2) | aktuell |
| Hessen | Wiesbaden (PvD) - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_50177.rss2) | prüfen: 2026-04-16 |
| Hessen | Wiesbaden - Polizeipräsidium Westhessen | [Feed](https://www.presseportal.de/rss/dienststelle_43562.rss2) | aktuell |
| Mecklenburg-Vorpommern | Bundespolizeiinspektion Kriminalitätsbekämpfung Rostock | [Feed](https://www.presseportal.de/rss/dienststelle_171964.rss2) | prüfen: 2026-10-01 |
| Mecklenburg-Vorpommern | Bundespolizeiinspektion Pasewalk mit Gemeinsamer deutsch-polnischer Dienststelle Pomellen | [Feed](https://www.presseportal.de/rss/dienststelle_70259.rss2) | aktuell |
| Mecklenburg-Vorpommern | Bundespolizeiinspektion Rostock | [Feed](https://www.presseportal.de/rss/dienststelle_50067.rss2) | aktuell |
| Mecklenburg-Vorpommern | Bundespolizeiinspektion See Warnemünde | [Feed](https://www.presseportal.de/rss/dienststelle_70261.rss2) | prüfen: 2026-06-10 |
| Mecklenburg-Vorpommern | Bundespolizeiinspektion Stralsund | [Feed](https://www.presseportal.de/rss/dienststelle_70258.rss2) | prüfen: 2026-10-12 |
| Mecklenburg-Vorpommern | Landeskriminalamt Mecklenburg-Vorpommern | [Feed](https://www.presseportal.de/rss/dienststelle_108748.rss2) | aktuell |
| Mecklenburg-Vorpommern | Landeswasserschutzpolizeiamt Mecklenburg-Vorpommern | [Feed](https://www.presseportal.de/rss/dienststelle_108749.rss2) | aktuell |
| Mecklenburg-Vorpommern | Polizeiinspektion Anklam | [Feed](https://www.presseportal.de/rss/dienststelle_108768.rss2) | prüfen: 2025-09-01 |
| Mecklenburg-Vorpommern | Polizeiinspektion Güstrow | [Feed](https://www.presseportal.de/rss/dienststelle_108766.rss2) | prüfen: 2024-08-27 |
| Mecklenburg-Vorpommern | Polizeiinspektion Ludwigslust | [Feed](https://www.presseportal.de/rss/dienststelle_108763.rss2) | prüfen: 2025-09-29 |
| Mecklenburg-Vorpommern | Polizeiinspektion Neubrandenburg | [Feed](https://www.presseportal.de/rss/dienststelle_108770.rss2) | prüfen: 2025-09-01 |
| Mecklenburg-Vorpommern | Polizeiinspektion Rostock | [Feed](https://www.presseportal.de/rss/dienststelle_108765.rss2) | prüfen: 2024-08-31 |
| Mecklenburg-Vorpommern | Polizeiinspektion Schwerin | [Feed](https://www.presseportal.de/rss/dienststelle_83338.rss2) | prüfen: 2024-08-30 |
| Mecklenburg-Vorpommern | Polizeiinspektion Stralsund | [Feed](https://www.presseportal.de/rss/dienststelle_108767.rss2) | prüfen: 2025-09-01 |
| Mecklenburg-Vorpommern | Polizeiinspektion Wismar | [Feed](https://www.presseportal.de/rss/dienststelle_108764.rss2) | prüfen: 2026-04-14 |
| Mecklenburg-Vorpommern | Polizeipräsidium Neubrandenburg | [Feed](https://www.presseportal.de/rss/dienststelle_108747.rss2) | aktuell |
| Mecklenburg-Vorpommern | Polizeipräsidium Rostock | [Feed](https://www.presseportal.de/rss/dienststelle_108746.rss2) | aktuell |
| Niedersachsen | Bundespolizeidirektion Hannover | [Feed](https://www.presseportal.de/rss/dienststelle_70246.rss2) | aktuell |
| Niedersachsen | Bundespolizeiinspektion Bad Bentheim | [Feed](https://www.presseportal.de/rss/dienststelle_70276.rss2) | aktuell |
| Niedersachsen | Bundespolizeiinspektion Flughafen Hannover | [Feed](https://www.presseportal.de/rss/dienststelle_74149.rss2) | aktuell |
| Niedersachsen | Bundespolizeiinspektion Hannover | [Feed](https://www.presseportal.de/rss/dienststelle_70388.rss2) | aktuell |
| Niedersachsen | Bundespolizeiinspektion See Cuxhaven | [Feed](https://www.presseportal.de/rss/dienststelle_70260.rss2) | prüfen: 2026-07-30 |
| Niedersachsen | Landeskriminalamt Niedersachsen | [Feed](https://www.presseportal.de/rss/dienststelle_105578.rss2) | aktuell |
| Niedersachsen | Polizei Braunschweig | [Feed](https://www.presseportal.de/rss/dienststelle_11554.rss2) | aktuell |
| Niedersachsen | Polizei Salzgitter | [Feed](https://www.presseportal.de/rss/dienststelle_56519.rss2) | aktuell |
| Niedersachsen | Polizei Wolfsburg | [Feed](https://www.presseportal.de/rss/dienststelle_56520.rss2) | aktuell |
| Niedersachsen | Polizeidirektion Göttingen | [Feed](https://www.presseportal.de/rss/dienststelle_7452.rss2) | prüfen: 2026-09-29 |
| Niedersachsen | Polizeidirektion Hannover | [Feed](https://www.presseportal.de/rss/dienststelle_66841.rss2) | aktuell |
| Niedersachsen | Polizeidirektion Lüneburg | [Feed](https://www.presseportal.de/rss/dienststelle_56836.rss2) | aktuell |
| Niedersachsen | Polizeidirektion Oldenburg | [Feed](https://www.presseportal.de/rss/dienststelle_62353.rss2) | prüfen: 2026-10-08 |
| Niedersachsen | Polizeidirektion Osnabrück | [Feed](https://www.presseportal.de/rss/dienststelle_104232.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Aurich/Wittmund | [Feed](https://www.presseportal.de/rss/dienststelle_104233.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Celle | [Feed](https://www.presseportal.de/rss/dienststelle_59457.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Cloppenburg/Vechta | [Feed](https://www.presseportal.de/rss/dienststelle_70090.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Cuxhaven | [Feed](https://www.presseportal.de/rss/dienststelle_68437.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Delmenhorst / Oldenburg - Land / Wesermarsch | [Feed](https://www.presseportal.de/rss/dienststelle_68438.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Diepholz | [Feed](https://www.presseportal.de/rss/dienststelle_68439.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Emsland/Grafschaft Bentheim | [Feed](https://www.presseportal.de/rss/dienststelle_104234.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Gifhorn | [Feed](https://www.presseportal.de/rss/dienststelle_56517.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Goslar | [Feed](https://www.presseportal.de/rss/dienststelle_56518.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Göttingen | [Feed](https://www.presseportal.de/rss/dienststelle_119508.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Hameln-Pyrmont/Holzminden | [Feed](https://www.presseportal.de/rss/dienststelle_57895.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Harburg | [Feed](https://www.presseportal.de/rss/dienststelle_59458.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Heidekreis | [Feed](https://www.presseportal.de/rss/dienststelle_59460.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Hildesheim | [Feed](https://www.presseportal.de/rss/dienststelle_57621.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Leer/Emden | [Feed](https://www.presseportal.de/rss/dienststelle_104235.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Lüneburg/Lüchow-Dannenberg/Uelzen | [Feed](https://www.presseportal.de/rss/dienststelle_59488.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Nienburg / Schaumburg | [Feed](https://www.presseportal.de/rss/dienststelle_57922.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Northeim | [Feed](https://www.presseportal.de/rss/dienststelle_57929.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Oldenburg-Stadt / Ammerland | [Feed](https://www.presseportal.de/rss/dienststelle_68440.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Osnabrück | [Feed](https://www.presseportal.de/rss/dienststelle_104236.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Rotenburg | [Feed](https://www.presseportal.de/rss/dienststelle_59459.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Stade | [Feed](https://www.presseportal.de/rss/dienststelle_59461.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Verden / Osterholz | [Feed](https://www.presseportal.de/rss/dienststelle_68441.rss2) | aktuell |
| Niedersachsen | Polizeiinspektion Wilhelmshaven/Friesland | [Feed](https://www.presseportal.de/rss/dienststelle_68442.rss2) | aktuell |
| Niedersachsen | Wasserschutzpolizeiinspektion Oldenburg | [Feed](https://www.presseportal.de/rss/dienststelle_119277.rss2) | prüfen: 2026-10-02 |
| Niedersachsen | Wasserschutzpolizeistation Nienburg | [Feed](https://www.presseportal.de/rss/dienststelle_165909.rss2) | prüfen: 2024-09-25 |
| Niedersachsen | Zentrale Polizeidirektion Braunschweig | [Feed](https://www.presseportal.de/rss/dienststelle_71298.rss2) | prüfen: 2020-09-14 |
| Niedersachsen | Zentrale Polizeidirektion Hannover | [Feed](https://www.presseportal.de/rss/dienststelle_71297.rss2) | prüfen: 2026-09-28 |
| Niedersachsen | Zentrale Polizeidirektion Lüneburg | [Feed](https://www.presseportal.de/rss/dienststelle_71301.rss2) | prüfen: 2021-03-30 |
| Niedersachsen | Zentrale Polizeidirektion Niedersachsen | [Feed](https://www.presseportal.de/rss/dienststelle_67812.rss2) | prüfen: 2025-06-23 |
| Niedersachsen | Zentrale Polizeidirektion Oldenburg | [Feed](https://www.presseportal.de/rss/dienststelle_71299.rss2) | prüfen: 2025-01-14 |
| Nordrhein-Westfalen | Bundespolizeidirektion Sankt Augustin | [Feed](https://www.presseportal.de/rss/dienststelle_70116.rss2) | aktuell |
| Nordrhein-Westfalen | Deutsche Hochschule der Polizei (DHPol) | [Feed](https://www.presseportal.de/rss/dienststelle_11025.rss2) | prüfen: 2014-07-29 |
| Nordrhein-Westfalen | Kreispolizeibehörde Borken | [Feed](https://www.presseportal.de/rss/dienststelle_24843.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Ennepe-Ruhr-Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_12726.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Euskirchen | [Feed](https://www.presseportal.de/rss/dienststelle_65841.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Heinsberg | [Feed](https://www.presseportal.de/rss/dienststelle_65845.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Herford | [Feed](https://www.presseportal.de/rss/dienststelle_65846.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Hochsauerlandkreis | [Feed](https://www.presseportal.de/rss/dienststelle_65847.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Höxter | [Feed](https://www.presseportal.de/rss/dienststelle_65848.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Kleve | [Feed](https://www.presseportal.de/rss/dienststelle_65849.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Märkischer Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_65850.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Oberbergischer Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_65843.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Olpe | [Feed](https://www.presseportal.de/rss/dienststelle_65852.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Rhein-Kreis Neuss | [Feed](https://www.presseportal.de/rss/dienststelle_65851.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Rhein-Sieg-Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_65853.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Siegen-Wittgenstein | [Feed](https://www.presseportal.de/rss/dienststelle_65854.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Soest | [Feed](https://www.presseportal.de/rss/dienststelle_65855.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Unna | [Feed](https://www.presseportal.de/rss/dienststelle_65856.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Viersen | [Feed](https://www.presseportal.de/rss/dienststelle_65857.rss2) | aktuell |
| Nordrhein-Westfalen | Kreispolizeibehörde Wesel | [Feed](https://www.presseportal.de/rss/dienststelle_65858.rss2) | aktuell |
| Nordrhein-Westfalen | Landesamt für Ausbildung, Fortbildung und Personalangelegenheiten der Polizei NRW | [Feed](https://www.presseportal.de/rss/dienststelle_29987.rss2) | prüfen: 2021-06-10 |
| Nordrhein-Westfalen | Landesamt für Zentrale Polizeiliche Dienste NRW | [Feed](https://www.presseportal.de/rss/dienststelle_67238.rss2) | aktuell |
| Nordrhein-Westfalen | Landeskriminalamt Nordrhein-Westfalen | [Feed](https://www.presseportal.de/rss/dienststelle_58451.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Aachen | [Feed](https://www.presseportal.de/rss/dienststelle_11559.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Bielefeld | [Feed](https://www.presseportal.de/rss/dienststelle_12522.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Bochum | [Feed](https://www.presseportal.de/rss/dienststelle_11530.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Bonn | [Feed](https://www.presseportal.de/rss/dienststelle_7304.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Coesfeld | [Feed](https://www.presseportal.de/rss/dienststelle_6006.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Dortmund | [Feed](https://www.presseportal.de/rss/dienststelle_4971.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Duisburg | [Feed](https://www.presseportal.de/rss/dienststelle_50510.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Düren | [Feed](https://www.presseportal.de/rss/dienststelle_8.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Düsseldorf | [Feed](https://www.presseportal.de/rss/dienststelle_13248.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Essen | [Feed](https://www.presseportal.de/rss/dienststelle_11562.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Gelsenkirchen | [Feed](https://www.presseportal.de/rss/dienststelle_51056.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Gütersloh | [Feed](https://www.presseportal.de/rss/dienststelle_23127.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Hagen | [Feed](https://www.presseportal.de/rss/dienststelle_30835.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Köln | [Feed](https://www.presseportal.de/rss/dienststelle_12415.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Lippe | [Feed](https://www.presseportal.de/rss/dienststelle_12727.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Mettmann | [Feed](https://www.presseportal.de/rss/dienststelle_43777.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Minden-Lübbecke | [Feed](https://www.presseportal.de/rss/dienststelle_43553.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Mönchengladbach | [Feed](https://www.presseportal.de/rss/dienststelle_30127.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Münster | [Feed](https://www.presseportal.de/rss/dienststelle_11187.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Rhein-Erft-Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_10374.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Rheinisch-Bergischer Kreis | [Feed](https://www.presseportal.de/rss/dienststelle_62459.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Steinfurt | [Feed](https://www.presseportal.de/rss/dienststelle_43526.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Warendorf | [Feed](https://www.presseportal.de/rss/dienststelle_52656.rss2) | aktuell |
| Nordrhein-Westfalen | Polizei Wuppertal | [Feed](https://www.presseportal.de/rss/dienststelle_11811.rss2) | aktuell |
| Nordrhein-Westfalen | Polizeipräsidium Hamm | [Feed](https://www.presseportal.de/rss/dienststelle_65844.rss2) | aktuell |
| Nordrhein-Westfalen | Polizeipräsidium Krefeld | [Feed](https://www.presseportal.de/rss/dienststelle_50667.rss2) | aktuell |
| Nordrhein-Westfalen | Polizeipräsidium Oberhausen | [Feed](https://www.presseportal.de/rss/dienststelle_62138.rss2) | aktuell |
| Nordrhein-Westfalen | Polizeipräsidium Recklinghausen | [Feed](https://www.presseportal.de/rss/dienststelle_42900.rss2) | aktuell |
| Rheinland-Pfalz | Bundespolizeidirektion Koblenz | [Feed](https://www.presseportal.de/rss/dienststelle_70137.rss2) | prüfen: 2026-10-08 |
| Rheinland-Pfalz | Bundespolizeiinspektion Kaiserslautern | [Feed](https://www.presseportal.de/rss/dienststelle_70139.rss2) | aktuell |
| Rheinland-Pfalz | Bundespolizeiinspektion Trier | [Feed](https://www.presseportal.de/rss/dienststelle_70138.rss2) | aktuell |
| Rheinland-Pfalz | Hochschule der Polizei | [Feed](https://www.presseportal.de/rss/dienststelle_117718.rss2) | aktuell |
| Rheinland-Pfalz | Landeskriminalamt Rheinland-Pfalz | [Feed](https://www.presseportal.de/rss/dienststelle_29763.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiautobahnstation Kaiserslautern und Zentrale Verkehrsdienste | [Feed](https://www.presseportal.de/rss/dienststelle_178880.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Bad Kreuznach | [Feed](https://www.presseportal.de/rss/dienststelle_117703.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Kaiserslautern | [Feed](https://www.presseportal.de/rss/dienststelle_117679.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Koblenz | [Feed](https://www.presseportal.de/rss/dienststelle_117712.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Landau | [Feed](https://www.presseportal.de/rss/dienststelle_117686.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Ludwigshafen | [Feed](https://www.presseportal.de/rss/dienststelle_117688.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Mainz | [Feed](https://www.presseportal.de/rss/dienststelle_117705.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Mayen | [Feed](https://www.presseportal.de/rss/dienststelle_117711.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Montabaur | [Feed](https://www.presseportal.de/rss/dienststelle_117710.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Neustadt/Weinstraße | [Feed](https://www.presseportal.de/rss/dienststelle_117687.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Neuwied/Rhein | [Feed](https://www.presseportal.de/rss/dienststelle_117709.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Pirmasens | [Feed](https://www.presseportal.de/rss/dienststelle_117677.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Trier | [Feed](https://www.presseportal.de/rss/dienststelle_117698.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Wittlich | [Feed](https://www.presseportal.de/rss/dienststelle_117697.rss2) | aktuell |
| Rheinland-Pfalz | Polizeidirektion Worms | [Feed](https://www.presseportal.de/rss/dienststelle_117702.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Alzey | [Feed](https://www.presseportal.de/rss/dienststelle_131673.rss2) | prüfen: 2026-06-19 |
| Rheinland-Pfalz | Polizeiinspektion Bingen | [Feed](https://www.presseportal.de/rss/dienststelle_131675.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Dahn | [Feed](https://www.presseportal.de/rss/dienststelle_178882.rss2) | prüfen: 2026-10-14 |
| Rheinland-Pfalz | Polizeiinspektion Ingelheim | [Feed](https://www.presseportal.de/rss/dienststelle_131671.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Kirchheimbolanden | [Feed](https://www.presseportal.de/rss/dienststelle_131674.rss2) | prüfen: 2026-05-29 |
| Rheinland-Pfalz | Polizeiinspektion Kirn | [Feed](https://www.presseportal.de/rss/dienststelle_131677.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Kusel und Polizeiwache Schönenberg-Kübelberg | [Feed](https://www.presseportal.de/rss/dienststelle_178879.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Landstuhl | [Feed](https://www.presseportal.de/rss/dienststelle_178876.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Lauterecken | [Feed](https://www.presseportal.de/rss/dienststelle_178877.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Oppenheim | [Feed](https://www.presseportal.de/rss/dienststelle_131672.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Rockenhausen | [Feed](https://www.presseportal.de/rss/dienststelle_178878.rss2) | aktuell |
| Rheinland-Pfalz | Polizeiinspektion Waldfischbach-Burgalben | [Feed](https://www.presseportal.de/rss/dienststelle_178883.rss2) | prüfen: 2026-10-07 |
| Rheinland-Pfalz | Polizeiinspektion Zweibrücken | [Feed](https://www.presseportal.de/rss/dienststelle_178881.rss2) | aktuell |
| Rheinland-Pfalz | Polizeipräsidium Einsatz, Logistik und Technik | [Feed](https://www.presseportal.de/rss/dienststelle_117719.rss2) | prüfen: 2026-10-11 |
| Rheinland-Pfalz | Polizeipräsidium Koblenz | [Feed](https://www.presseportal.de/rss/dienststelle_117715.rss2) | aktuell |
| Rheinland-Pfalz | Polizeipräsidium Mainz | [Feed](https://www.presseportal.de/rss/dienststelle_117708.rss2) | aktuell |
| Rheinland-Pfalz | Polizeipräsidium Rheinpfalz | [Feed](https://www.presseportal.de/rss/dienststelle_117696.rss2) | aktuell |
| Rheinland-Pfalz | Polizeipräsidium Trier | [Feed](https://www.presseportal.de/rss/dienststelle_117701.rss2) | aktuell |
| Rheinland-Pfalz | Polizeipräsidium Westpfalz | [Feed](https://www.presseportal.de/rss/dienststelle_117683.rss2) | aktuell |
| Saarland | Bundespolizeiinspektion Saarbrücken | [Feed](https://www.presseportal.de/rss/dienststelle_70140.rss2) | aktuell |
| Saarland | Landespolizeidirektion Saarland | [Feed](https://www.presseportal.de/rss/dienststelle_120462.rss2) | aktuell |
| Saarland | Polizeiinspektion Homburg | [Feed](https://www.presseportal.de/rss/dienststelle_138521.rss2) | aktuell |
| Saarland | Polizeiinspektion Lebach | [Feed](https://www.presseportal.de/rss/dienststelle_138502.rss2) | prüfen: 2026-09-26 |
| Saarland | Polizeiinspektion Merzig | [Feed](https://www.presseportal.de/rss/dienststelle_138504.rss2) | aktuell |
| Saarland | Polizeiinspektion Neunkirchen | [Feed](https://www.presseportal.de/rss/dienststelle_138511.rss2) | aktuell |
| Saarland | Polizeiinspektion Nordsaarland | [Feed](https://www.presseportal.de/rss/dienststelle_138505.rss2) | aktuell |
| Saarland | Polizeiinspektion Saarbrücken-Burbach | [Feed](https://www.presseportal.de/rss/dienststelle_138341.rss2) | prüfen: 2026-10-01 |
| Saarland | Polizeiinspektion Saarbrücken-Stadt | [Feed](https://www.presseportal.de/rss/dienststelle_138303.rss2) | aktuell |
| Saarland | Polizeiinspektion Saarlouis | [Feed](https://www.presseportal.de/rss/dienststelle_138489.rss2) | aktuell |
| Saarland | Polizeiinspektion Sankt Ingbert | [Feed](https://www.presseportal.de/rss/dienststelle_138534.rss2) | aktuell |
| Saarland | Polizeiinspektion Sankt Wendel | [Feed](https://www.presseportal.de/rss/dienststelle_138507.rss2) | aktuell |
| Saarland | Polizeiinspektion Sulzbach | [Feed](https://www.presseportal.de/rss/dienststelle_138473.rss2) | aktuell |
| Saarland | Polizeiinspektion Völklingen | [Feed](https://www.presseportal.de/rss/dienststelle_138422.rss2) | aktuell |
| Sachsen | Bundespolizeiinspektion Berggießhübel | [Feed](https://www.presseportal.de/rss/dienststelle_74163.rss2) | aktuell |
| Sachsen | Bundespolizeiinspektion Chemnitz | [Feed](https://www.presseportal.de/rss/dienststelle_74164.rss2) | prüfen: 2026-10-14 |
| Sachsen | Bundespolizeiinspektion Dresden | [Feed](https://www.presseportal.de/rss/dienststelle_74162.rss2) | aktuell |
| Sachsen | Bundespolizeiinspektion Ebersbach | [Feed](https://www.presseportal.de/rss/dienststelle_74161.rss2) | aktuell |
| Sachsen | Bundespolizeiinspektion Klingenthal | [Feed](https://www.presseportal.de/rss/dienststelle_74166.rss2) | prüfen: 2026-07-02 |

## Gemischte Blaulichtfeeds – getrennt von Polizeifeeds

Das [Presseportal-RSS-Verzeichnis](https://www.presseportal.de/rss/) bietet einen Gesamtfeed und Länderfeeds. Sie können auch Feuerwehr, Rettungsdienst oder andere Organisationen enthalten. Berlin und Brandenburg werden dort gemeinsam geführt.

| Abdeckung | RSS |
|---|---|
| Blaulicht | [Feed](https://www.presseportal.de/rss/polizei.rss2) |
| Baden-Württemberg | [Feed](https://www.presseportal.de/rss/polizei/laender/1.rss2) |
| Bayern | [Feed](https://www.presseportal.de/rss/polizei/laender/2.rss2) |
| Berlin/Brandenburg | [Feed](https://www.presseportal.de/rss/polizei/laender/3.rss2) |
| Bremen | [Feed](https://www.presseportal.de/rss/polizei/laender/4.rss2) |
| Hamburg | [Feed](https://www.presseportal.de/rss/polizei/laender/5.rss2) |
| Hessen | [Feed](https://www.presseportal.de/rss/polizei/laender/6.rss2) |
| Mecklenburg-Vorpommern | [Feed](https://www.presseportal.de/rss/polizei/laender/7.rss2) |
| Niedersachsen | [Feed](https://www.presseportal.de/rss/polizei/laender/8.rss2) |
| Nordrhein-Westfalen | [Feed](https://www.presseportal.de/rss/polizei/laender/9.rss2) |
| Rheinland-Pfalz | [Feed](https://www.presseportal.de/rss/polizei/laender/10.rss2) |
| Saarland | [Feed](https://www.presseportal.de/rss/polizei/laender/13.rss2) |
| Sachsen | [Feed](https://www.presseportal.de/rss/polizei/laender/14.rss2) |
| Sachsen-Anhalt | [Feed](https://www.presseportal.de/rss/polizei/laender/16.rss2) |
| Schleswig-Holstein | [Feed](https://www.presseportal.de/rss/polizei/laender/11.rss2) |
| Thüringen | [Feed](https://www.presseportal.de/rss/polizei/laender/15.rss2) |

## Grenzen und besondere Fälle

- **Bundespolizei:** Zum ursprünglichen Recherchestand 2026-10-28 kündigte die [offizielle Presseseite](https://bundespolizei.de/presse/pressemitteilungen) den eigenen RSS-Feed als künftig wieder verfügbar an und verwies auf das Presseportal. Der Hinweis ersetzt keine erneute Prüfung der Webseite. Geprüfte Bundespolizei-Feeds über Presseportal sind oben enthalten.
- **Sachsen:** Die [offizielle Polizei-Seite](https://www.polizei.sachsen.de/de/presseinfo_aktuell.asp) nennt RSS über den Medienservice nach Registrierung. Ein frei zugänglicher landesweiter Behördenfeed wurde hier nicht bestätigt. Presseportal-Einträge aus Sachsen enthalten unter anderem Bundespolizei; das ist keine vollständige Abdeckung der sächsischen Landespolizei.
- **Vorübergehende Abruffehler:** Einzelne Presseportal-Adressen können vorübergehend HTTP 503 liefern. Diese wurden nicht als funktionierende Feeds ausgegeben. Daraus folgt keine dauerhafte Abschaltung oder ein fehlendes Angebot für das betreffende Bundesland.
- **14-Tage-Schwelle:** Ein älterer letzter Eintrag kann bei selten berichtenden Dienststellen normal sein. Solche Feeds stehen mit Prüfstatus im JSON, nicht in der OPML.
- **Quellenrolle:** Polizeipresse ist eine behördliche Darstellung. Dieselbe Meldung auf Behörden-Webseite und Presseportal ist keine unabhängige Gegenrecherche.
- **Geografie:** Die Bundesland-Einordnung kommt aus dem Presseportal-Verzeichnis. Einzelne Bundesbehörden und Bundespolizeidienststellen können auch über andere Länder berichten.
- **Nutzung:** Feed-Erreichbarkeit ist keine pauschale Lizenz für Artikel, Bilder oder personenbezogene Angaben. Die Quellenauswahl bleibt unverändert.

Die Recherche ist mit den Skripten unter `research/police-rss/` reproduzierbar. Im Prüfprotokoll werden ausschließlich technische Kennwerte und Feed-Metadaten gespeichert, keine vollständigen Meldungstexte.

<!-- emergency-extension -->

## Erweiterung: Feuerwehr, Rettungsdienst und Warnungen

| Kategorie | Feeds gesamt | Im OPML-Import |
|---|---:|---:|
| Feuerwehr | 197 | 94 |
| Katastrophenschutz | 7 | 2 |
| Rettungsdienst | 7 | 3 |
| Warnungen | 3 | 3 |
| Wetter / Naturgefahren | 4 | 4 |

Die Feuerwehr- und THW-Feeds des [Presseportal-Dienststellenverzeichnisses](https://www.presseportal.de/blaulicht/dienststellen) wurden aus dem bereits gespeicherten Prüfprotokoll übernommen. Neue Organisations- und Warnquellen wurden direkt geladen und auf gültiges RSS/Atom geprüft. Organisationsmeldungen von Rettungsdiensten können auch Ausbildung, Verbandspolitik oder humanitäre Hilfe betreffen; sie sind kein öffentliches vollständiges Rettungseinsatzprotokoll.

### Warnfeeds: andere Bedeutung als Einsatznachrichten

Amtliche Warnungen enthalten Gültigkeitszeiträume, betroffene Gebiete und gegebenenfalls Aktualisierungen oder Entwarnungen. Ein technisch lesbarer Feed mit Einträgen beweist keine aktuell gültige Warnung. Ein leerer Warnfeed ist nicht automatisch defekt; daraus allein wird auch keine Entwarnung abgeleitet. Für die Sendung ist ein zusätzlicher Warnungsadapter erforderlich, der diese Angaben auswertet. Es wurde kein Warnsystem aktiviert.

Geprüfte Quellen sind unter anderem die [DWD CAP-Feeds](https://www.dwd.de/DE/leistungen/opendata/help/warnungen/dwd_warnings_products_overview_en_pdf.pdf?__blob=publicationFile&v=3), [MeteoAlarm](https://api.meteoalarm.org/) für Österreich und Deutschland, das [Hochwasserportal](https://www.hochwasserzentralen.de/) sowie ortsbezogene BBK-/MoWaS-RSS-Feeds. Das [BBK beschreibt RSS für die Ortsauswahl](https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warn-App-NINA/warn-app-nina_node.html). Berlin, Hamburg und München werden als Beispiel-Adressen geprüft; nur technisch bestätigte Feeds erscheinen unten. Sie decken nicht ganz Deutschland ab.

| Kategorie | Land / Region | Organisation / Kanal | Feed | Prüfung |
|---|---|---|---|---|
| Feuerwehr | DE / Bundesbehörden | Freiwillige Feuerwehr Stadt Petershagen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_181147.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Weinheim | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_179375.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Allensbach | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_175384.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Bad Säckingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140463.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Landesfeuerwehrverband Baden-Württemberg e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139254.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Böblingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_164917.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Kreisfeuerwehrverband Calw e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116896.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Eigeltingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139087.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehren im Landkreis Esslingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_177478.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Gundelfingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_179865.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Gäufelden | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139748.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Kreisfeuerwehrverband Landkreis Karlsruhe | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130685.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Konstanz | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139089.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Offenburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_128693.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Pforzheim | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_151867.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Radolfzell | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_169982.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehren des Landkreises Ravensburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_153641.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Reichenau | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_163367.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Kreisfeuerwehrverband Rhein-Neckar-Kreis e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_171818.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Kreisfeuerwehrverband Sigmaringen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140932.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Stockach | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134581.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Stuttgart | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_161590.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Kreisfeuerwehrverband Bodenseekreis e. V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_127207.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Walldorf | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134197.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Feuerwehr Weil am Rhein | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_182024.rss2) | aktuell |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Weil der Stadt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140948.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Baden-Württemberg | Freiwillige Feuerwehr Überlingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_182292.rss2) | aktuell |
| Katastrophenschutz | DE / Bayern | THW Landesverband Bayern | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_102101.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Bayern | Feuerwehr München | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_131419.rss2) | aktuell |
| Feuerwehr | DE / Bayern | Feuerwehr Nürnberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_171957.rss2) | Aktualität prüfen |
| Katastrophenschutz | DE / Berlin/Brandenburg | THW Landesverband Berlin, Brandenburg, Sachsen-Anhalt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_129178.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Bremen | Feuerwehr Bremen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130368.rss2) | aktuell |
| Feuerwehr | DE / Bremen | Feuerwehr Bremerhaven | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_133092.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Hamburg | Feuerwehr Hamburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_82522.rss2) | aktuell |
| Feuerwehr | DE / Hessen | Feuerwehr Frankfurt am Main | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116052.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Hessen | Kreisfeuerwehrverband Main-Taunus e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_172530.rss2) | aktuell |
| Rettungsdienst | DE / Hessen | Feuerwehr, Katastrophenschutz und Rettungsdienst Rheingau-Taunus-Kreis | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_164802.rss2) | aktuell |
| Feuerwehr | DE / Hessen | Freiwillige Feuerwehr Rüdesheim | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_163012.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Mecklenburg-Vorpommern | Feuerwehr Rostock | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_175951.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Aurich | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_178159.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr der Stadt Bergen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_180505.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Celle | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_149821.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Feuerwehr Flotwedel | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_148638.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Samtgemeinde Fredenbeck | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_141183.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Feuerwehr Stadt Geestland | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_182355.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Hambühren | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_174712.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Feuerwehr Hannover | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_169586.rss2) | aktuell |
| Katastrophenschutz | DE / Niedersachsen | THW Landesverband Bremen, Niedersachsen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_147101.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Feuerwehr Helmstedt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_154352.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Kreisfeuerwehr Oldenburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_172811.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Feuerwehr Landkreis Leer | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_122785.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Lehrte | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_131348.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Kreisfeuerwehrverband Lüchow-Dannenberg e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_160169.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Osterholz-Scharmbeck | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_154802.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Niedersachsen | Kreisfeuerwehr Rotenburg (Wümme) | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134804.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Gemeinde Schiffdorf | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118388.rss2) | aktuell |
| Feuerwehr | DE / Niedersachsen | Freiwillige Feuerwehr Südheide | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_177692.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Siegen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_158946.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Burscheid | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_171447.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Ahlen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_119855.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr der Gemeinde Alfter | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140203.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Alpen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_131475.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Altena | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_183084.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Altenbeken | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118012.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr der Stadt Arnsberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116297.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Attendorn | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116323.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Bad Honnef | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_133680.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Bad Oeynhausen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_182385.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Bad Salzuflen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_135948.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Bedburg-Hau | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116244.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Bergheim | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_168361.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Bergisch Gladbach | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116240.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Beverungen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_169083.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Bocholt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_146407.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Bochum | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115868.rss2) | aktuell |
| Rettungsdienst | DE / Nordrhein-Westfalen | Feuerwehr und Rettungsdienst Bonn | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115888.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Borgentreich | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_126110.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Bottrop | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115891.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Breckerfeld | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69791.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Datteln | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130639.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Detmold | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116239.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Dinslaken | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116534.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Dorsten | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116242.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Dortmund | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115869.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Drolshagen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_122862.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Dörentrup | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_179920.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Dülmen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118670.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Düren | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134173.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Düsseldorf | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115876.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Kreisfeuerwehrverband Ennepe-Ruhr e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69247.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Ennepetal | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69780.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Ense | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_173619.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Erkrath | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116243.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Essen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_56893.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Finnentrop | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_165856.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Frechen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_164642.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Gangelt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130424.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Gelsenkirchen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116260.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Gevelsberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69782.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Gladbeck | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_117806.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr der Stadt Goch | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_126714.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Greven | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_178564.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Grevenbroich | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134498.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Gronau | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_172683.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Haan | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116238.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Hagen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_129251.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Stadtfeuerwehrverband Hagen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115870.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Hamminkeln | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_165122.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Hattingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69779.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Heiligenhaus | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116231.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Herdecke | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69790.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Horn-Bad Meinberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_153423.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Hüllhorst | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_135251.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Hünxe | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_133631.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Stadt Hürth | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_141881.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Institut der Feuerwehr NRW | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_160795.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Iserlohn | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116234.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Kaarst | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116230.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Kalkar | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_126309.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Kamen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139081.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Kerpen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116241.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Kirchhundem | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116945.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Kleve | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_126799.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Kranenburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_145404.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Krefeld | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115878.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Kreuzau | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140204.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Köln | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115889.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Königswinter | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_128175.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Lage | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_117388.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Leichlingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_175364.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Lennestadt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118009.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Leopoldshöhe | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_119364.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Leverkusen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115890.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr der Stadt Lohmar | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118806.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Lüdenscheid | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116354.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Lügde | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_121193.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Mechernich | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_179776.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Meerbusch | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116674.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Menden | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_119161.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Mettmann | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_119015.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Minden | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_152228.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Moers | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_156944.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Mönchengladbach | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115879.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Mülheim an der Ruhr | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115880.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Neukirchen-Vluyn | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_178336.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Neuss | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_122045.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Stadt Nideggen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_134198.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Oberhausen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115881.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Oer-Erkenschwick | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116581.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Olpe | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116237.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Plettenberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116600.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Porta Westfalica | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_178063.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Pulheim | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_156611.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Ratingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_70701.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Recklinghausen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_119285.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Remscheid | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115882.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Gemeinde Rheurdt | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130323.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Rösrath | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_130257.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Sankt Augustin | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_127035.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Schalksmühle | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_120413.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Schermbeck | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118232.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Schwelm | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69781.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Selfkant | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140388.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehren im Kreis Soest | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_129590.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Solingen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115884.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr der Gemeinde Sonsbeck | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_140447.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Sprockhövel | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69788.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Stolberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116325.rss2) | Aktualität prüfen |
| Katastrophenschutz | DE / Nordrhein-Westfalen | Bundesanstalt Technisches Hilfswerk - Landesverbandsdienststelle Nordrhein-Westfalen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_179236.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Tönisvorst | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_128354.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Velbert | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_118285.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Voerde | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_125427.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Wachtberg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_163172.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Weeze | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_126307.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Wenden | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_128090.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Werne | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_116730.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Wetter (Ruhr) | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_69783.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Freiwillige Feuerwehr Hansestadt Wipperfürth | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_139090.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Witten | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_120429.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Wuppertal | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_115885.rss2) | aktuell |
| Feuerwehr | DE / Nordrhein-Westfalen | Verband der Feuerwehren in NRW e. V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_78309.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Nordrhein-Westfalen | Feuerwehr Xanten | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_122220.rss2) | aktuell |
| Feuerwehr | DE / Rheinland-Pfalz | Feuerwehr VG Asbach | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_133489.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Rheinland-Pfalz | Freiwillige Feuerwehr Frankenthal | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_136510.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Rheinland-Pfalz | Feuerwehr Ludwigshafen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_135123.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Rheinland-Pfalz | Feuerwehr Mainz | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_171463.rss2) | aktuell |
| Feuerwehr | DE / Rheinland-Pfalz | Feuerwehren VG Westerburg | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_172221.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Saarland | Kreisfeuerwehrverband Neunkirchen | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_169726.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Sachsen | Landesfeuerwehrverband Sachsen e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_153421.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Sachsen | Kreisfeuerwehrverband Landkreis Leipzig | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_167369.rss2) | Aktualität prüfen |
| Feuerwehr | DE / Sachsen | Feuerwehr Dresden | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_154636.rss2) | aktuell |
| Feuerwehr | DE / Sachsen | Kreisfeuerwehrverband Görlitz e.V. | [RSS/Atom](https://www.presseportal.de/rss/dienststelle_169679.rss2) | Aktualität prüfen |
| Wetter / Naturgefahren | AT / Österreich | MeteoAlarm Österreich | [RSS/Atom](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-austria) | Warnfeed technisch lesbar |
| Wetter / Naturgefahren | DE / Deutschland | MeteoAlarm Deutschland | [RSS/Atom](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-germany) | Warnfeed technisch lesbar |
| Wetter / Naturgefahren | DE / Deutschland | DWD – amtliche Wetterwarnungen | [RSS/Atom](https://www.dwd.de/DWD/warnungen/cap-feed/de/rss.xml) | Warnfeed technisch lesbar |
| Warnungen | DE / Berlin | BBK / NINA / MoWaS – Berlin | [RSS/Atom](https://warnung.bund.de/api31/mowas/rss/110000000000.rss) | leer, technisch lesbar |
| Warnungen | DE / Hamburg | BBK / NINA / MoWaS – Hamburg | [RSS/Atom](https://warnung.bund.de/api31/mowas/rss/020000000000.rss) | leer, technisch lesbar |
| Warnungen | DE / Bayern | BBK / NINA / MoWaS – München | [RSS/Atom](https://warnung.bund.de/api31/mowas/rss/091620000000.rss) | leer, technisch lesbar |
| Wetter / Naturgefahren | DE / Deutschland | Länderübergreifendes Hochwasserportal | [RSS/Atom](https://www.hochwasserzentralen.de/rss) | Warnfeed technisch lesbar |
| Feuerwehr | AT / Österreich | ÖBFV | [RSS/Atom](https://www.bundesfeuerwehrverband.at/feed/) | aktuell |
| Feuerwehr | AT / Steiermark | Landesfeuerwehrverband Steiermark - Aktuelles | [RSS/Atom](https://www.lfv.steiermark.at/contentxxl/services/newsexport/rss.asmx/GetRSSNewsByTabId?tabid=17) | aktuell |
| Feuerwehr | AT / Burgenland | Freiwillige Feuerwehr Neutal | [RSS/Atom](https://www.feuerwehr-neutal.at/feed/) | aktuell |
| Rettungsdienst | AT / Österreich | ÖBRD – Bundesverband | [RSS/Atom](https://bergrettung.at/feed/) | Aktualität prüfen |
| Rettungsdienst | AT / Steiermark | Bergrettung Steiermark | [RSS/Atom](https://bergrettung-stmk.at/feed/) | Aktualität prüfen |
| Rettungsdienst | AT / Österreich | owr.at | [RSS/Atom](https://owr.at/feed/) | aktuell |
| Rettungsdienst | DE / Deutschland | DRK Pressemitteilungen | [RSS/Atom](https://www.drk.de/presse.rss) | aktuell |
| Rettungsdienst | DE / Schleswig-Holstein | DLRG Schleswig-Holstein e.V. | [RSS/Atom](https://schleswig-holstein.dlrg.de/nachrichten/nachrichtenarchiv/newsfeed.xml?tx_dlrgnews_pi3%5Baction%5D=xml&tx_dlrgnews_pi3%5Bfeed_id%5D=1296250&cHash=c61f6572b65257ababebb946e0f80043) | Aktualität prüfen |
| Feuerwehr | DE / Deutschland | Feuerwehrverband | [RSS/Atom](https://www.feuerwehrverband.de/feed/) | aktuell |
| Feuerwehr | DE / Hessen | Pressemeldungen LFV Hessen | [RSS/Atom](https://www.feuerwehr-hessen.de/feed/presse-lfv-hesssen.xml) | aktuell |
| Feuerwehr | DE / Hessen | Fachinformationen LFV Hessen | [RSS/Atom](https://www.feuerwehr-hessen.de/feed/fachinformationen-lfv-hessen.xml) | Aktualität prüfen |
| Feuerwehr | DE / Hessen | LFV Infodienst | [RSS/Atom](https://www.feuerwehr-hessen.de/feed/feuerwehr-hessen-infodienst.xml) | Aktualität prüfen |
| Feuerwehr | DE / Hessen | Aktuelles von Landesfeuerwehrverband Hessen | [RSS/Atom](https://www.feuerwehr-hessen.de/feed/feuerwehr-hessen-alle-news.xml) | aktuell |
| Feuerwehr | DE / Berlin | Berliner Feuerwehr - Einsätze | [RSS/Atom](https://www.berliner-feuerwehr.de/aktuelles/einsaetze/einsaetze-rss?type=9818) | aktuell |
| Feuerwehr | DE / Berlin | Berliner Feuerwehr - Aktuelles | [RSS/Atom](https://www.berliner-feuerwehr.de/aktuelles/nachrichten/nachrichten-rss?type=9818) | Aktualität prüfen |
| Feuerwehr | DE / Berlin | Berliner Feuerwehr - Presseinformationen | [RSS/Atom](https://www.berliner-feuerwehr.de/aktuelles/presseinformationen/presseinfo-rss?type=9818) | Aktualität prüfen |
| Katastrophenschutz | DE / Deutschland | THW - RSS-Feed mit aktuellen Einsätzen | [RSS/Atom](https://www.thw.de/SiteGlobals/Functions/RSS/DE/RSSNewsfeed_Einsaetze.xml) | Aktualität prüfen |
| Katastrophenschutz | DE / Deutschland | THW - RSS-Feed mit aktuellen Meldungen | [RSS/Atom](https://www.thw.de/SiteGlobals/Functions/RSS/DE/RSSNewsfeed_Meldungen.xml) | aktuell |
| Katastrophenschutz | DE / Deutschland | THW - RSS-Feed mit aktuellen Pressemitteilungen | [RSS/Atom](https://www.thw.de/SiteGlobals/Functions/RSS/DE/RSSNewsfeed_Pressemitteilungen.xml) | aktuell |

### Landeswarnzentralen und zusätzliche Web-/API-Quellen

Die österreichischen Landeswarn-/Lagezentralen und Warnsysteme sind mit ihren offiziellen Fundstellen erfasst. Wo kein spezifischer öffentlicher RSS-/Atom-Feed bestätigt wurde, steht ausdrücklich „zusätzliche Anbindung nötig“. Allgemeine Landesnachrichtenfeeds werden nicht als Warnfeed ausgegeben.

AT-Alert ist die öffentliche behördliche Warnseite der [RTR](https://www.rtr.at/rtr/service/at_alert/at_alert_startseite.de.html). [GeoSphere](https://data.hub.geosphere.at/dataset/warnungen-v1) dokumentiert eine Wetterwarnungs-API. Diese Quellen werden nicht als RSS-Adressen ausgegeben. Öffentliche Einsatzübersichten etwa der LSZ Burgenland oder LAWZ Kärnten sind außerdem keine vollständigen Echtzeitwarnungen. Die [Nutzungshinweise der LAWZ Kärnten](https://alarmierungen.feuerwehr-ktn.at/termsOfUse.html) erläutern Verzögerungen und die Abgrenzung zu amtlichen Warnungen.

| Bereich | Land / Region | Quelle | Technischer Stand |
|---|---|---|---|
| Landeswarnzentralen | AT / Burgenland | [Landessicherheitszentrale Burgenland](https://www.lsz-b.at/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Burgenland | [LSZ Burgenland – Einsatzübersicht](https://einsatz.lsz-b.at/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Niederösterreich | [Landeswarnzentrale Niederösterreich](https://www.noel.gv.at/noe/Katastrophenschutz/Landeswarnzentrale.html) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Oberösterreich | [Landeswarnzentrale Oberösterreich](https://www.ooelfv.at/das-kommando/standorte/ooe-landeswarnzentrale) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Kärnten | [Landesalarm- und Warnzentrale Kärnten](https://www.feuerwehr-ktn.at/verband/lawz/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Kärnten | [LAWZ Kärnten – öffentliche Einsatzübersicht](https://alarmierungen.feuerwehr-ktn.at/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Steiermark | [Landeswarnzentrale Steiermark](https://www.verwaltung.steiermark.at/cms/ziel/75757731/DE/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Salzburg | [Landesalarm- und Warnzentrale Salzburg](https://www.salzburg.gv.at/themen/sicherheit/katastrophenschutz) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Tirol | [Landes-Warn- und Lagezentrum Tirol](https://www.tirol.gv.at/sicherheit/kkm/krisen-und-gefahrenmanagement/landes-warn-und-lagezentrum/erreichbarkeit-und-dienstbetrieb/) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Vorarlberg | [Landeswarnzentrale Vorarlberg](https://vorarlberg.at/-/landeswarnzentrale) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Vorarlberg | [Warndienste Vorarlberg](https://warnung.vorarlberg.at/vtgdb/dist/index.html) | Web/API; zusätzliche Anbindung nötig |
| Landeswarnzentralen | AT / Wien | [Wien – Warn- und Alarmsystem / Krisenmanagement](https://www.wien.gv.at/zusammenleben/sirenen-probealarme) | Web/API; zusätzliche Anbindung nötig |
| Warnungen | AT / Österreich | [AT-Alert – behördliche Warnungen](https://warnung.at-alert.at/de) | Web/API; zusätzliche Anbindung nötig |
| Wetter / Naturgefahren | AT / Österreich | [GeoSphere Austria – Wetterwarnungen](https://data.hub.geosphere.at/dataset/warnungen-v1) | Web/API; zusätzliche Anbindung nötig |
| Wetter / Naturgefahren | AT / Österreich | [Lawinenwarndienste Österreich](https://www.lawinen.at/) | Web/API; zusätzliche Anbindung nötig |
| Wetter / Naturgefahren | AT / Tirol | [Europaregion – Lawinenbericht](https://avalanche.report/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Oberösterreich | [LFV Oberösterreich](https://www.ooelfv.at/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Niederösterreich | [NÖ Landesfeuerwehrverband](https://www.noe122.at/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Tirol | [LFV Tirol](https://www.lfv-tirol.at/) | Abruf nicht bestätigt; prüfen |
| Feuerwehr | AT / Kärnten | [LFV Kärnten](https://www.feuerwehr-ktn.at/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Vorarlberg | [LFV Vorarlberg](https://www.lfv-vorarlberg.at/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Salzburg | [LFV Salzburg](https://www.lfv-sbg.at/) | Web/API; zusätzliche Anbindung nötig |
| Feuerwehr | AT / Burgenland | [LFV Burgenland](https://www.lfv-bgld.at/) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | AT / Österreich | [Österreichisches Rotes Kreuz](https://www.roteskreuz.at/home) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | AT / Österreich | [Samariterbund Österreich](https://www.samariterbund.net/) | Abruf nicht bestätigt; prüfen |
| Rettungsdienst | AT / Österreich | [Johanniter Österreich](https://www.johanniter.at/) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | DE / Sachsen-Anhalt | [DRK Sachsen-Anhalt](https://www.sachsen-anhalt.drk.de/footer-menue-deutsch/service/sitemap.html) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | DE / Deutschland | [Johanniter-Unfall-Hilfe](https://www.johanniter.de/presse/) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | DE / Deutschland | [Malteser Hilfsdienst](https://www.malteser.de/) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | DE / Deutschland | [Arbeiter-Samariter-Bund](https://www.asb.de/) | Web/API; zusätzliche Anbindung nötig |
| Rettungsdienst | DE / Deutschland | [DLRG](https://www.dlrg.de/informieren/die-dlrg/presse/) | Web/API; zusätzliche Anbindung nötig |

Zusätzliche technische Ergebnisse: [emergency-checks.json](../../research/police-rss/emergency-checks.json). Die bereits zuvor dokumentierten Polizeifeeds und ihre Prüfdaten bleiben erhalten. Die aktive Sendungskonfiguration wurde nicht geändert.
