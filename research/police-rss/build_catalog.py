#!/usr/bin/env python3
"""Create separate police and mixed-emergency catalogues without enabling feeds."""
import collections
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def police(r):
 title=r.get('feed_title','').casefold()
 return bool(re.search('polizei|police|kriminalamt',title)) and not re.search('gewerkschaft|polizeiakademie|stiftung|verein',title)

def main():
 raw=json.loads((HERE/'checks.json').read_text());feeds=[];mixed=[];related=[];excluded=[];seen=set()
 for r in raw['feeds']:
  kind=r['source_type']
  if r['status']!='valid':continue
  if kind=='pressportal_station' and not police(r):
   excluded.append({'url':r['url'],'name':r.get('feed_title'), 'reason':'Keine polizeiliche Pressestelle (z. B. Feuerwehr, Rettungsdienst, Zoll oder Gewerkschaft)'});continue
  if kind=='authority' and re.search('/(fahndungen|termine|stellenausschreibungen)/',r['url']):
   excluded.append({'url':r['url'],'reason':'Keine laufenden Polizeipresse-Meldungen'});continue
  url=r.get('resolved_url',r['url'])
  if url in seen:continue
  seen.add(url)
  title=r.get('feed_title','').removeprefix('Presseportal.de - ')
  region=r['region']
  if kind=='pressportal_mixed':region=title.removeprefix('Presseportal.de - ');title='Blaulicht – '+region
  notes=[]
  if r['freshness']=='stale':notes.append('Keine datierte Meldung innerhalb von 14 Tagen; kann selten publizierende Pressestelle sein.')
  elif r['freshness']=='undated':notes.append('Keine auswertbaren Meldungsdaten, Aktualität nicht automatisch bestätigt.')
  elif r['freshness']=='future_date':notes.append('Meldungsdatum liegt mehr als zwei Tage in der Zukunft.')
  if not url.startswith('https://'):notes.append('Weiterleitung auf HTTP.')
  if r.get('item_count') and not r.get('items_with_article_link'):notes.append('Keine direkten Artikel-Links in den geprüften Meldungen; Beschreibung/Summary als Textquelle verwenden.')
  atom=next((a for a in raw['atom_variants'] if a.get('variant_of')==r['url']),None)
  e={'id':hashlib.sha256(url.encode()).hexdigest()[:12],'publisher':title,'name':title,'url':url,'language':'de','declared_language':r.get('declared_language',''),'publisher_country':r['country'],'region':region,'topic':'Polizei' if kind not in ('pressportal_mixed','authority_related') else 'Blaulicht gemischt' if kind=='pressportal_mixed' else 'Innenressort / Sicherheitsbehörden','suggested_section':'local','source_type':kind,'format':r['format'],'status':'verified_recent' if r['freshness']=='recent' and url.startswith('https://') else 'review','checked_at':r['checked_at'],'newest_item_at':r.get('newest_item_at'),'item_count':r['item_count'],'items_with_article_link':r['items_with_article_link'],'median_summary_chars':r['median_summary_chars'],'evidence_url':r['evidence_url'],'notes':notes,'enabled_by_default':False}
  if atom:e.update(atom_url=r['atom_url'],atom_status=atom['status'])
  (mixed if kind=='pressportal_mixed' else related if kind=='authority_related' else feeds).append(e)
 feeds.sort(key=lambda e:(e['publisher_country'],e['source_type']!='authority',e['region'],e['name']))
 active=[f for f in feeds if f['status']=='verified_recent']
 counts={'police_feeds':len(feeds),'current_police_feeds':len(active),'review_police_feeds':len(feeds)-len(active),'austrian_police_feeds':sum(f['publisher_country']=='AT' for f in feeds),'german_police_feeds':sum(f['publisher_country']=='DE' for f in feeds),'mixed_blaulicht_feeds':len(mixed),'related_authority_feeds':len(related),'candidate_urls_checked':len(raw['feeds']),'atom_variants_checked':len(raw['atom_variants'])}
 data={'schema_version':1,'researched_on':raw['researched_on'],'method':raw['method'],'freshness_days':14,'counts':counts,'feeds':feeds,'mixed_feeds':mixed,'related_authority_feeds':related,'excluded':excluded,'limitations':['Behördenmitteilungen und ihre Presseportal-Veröffentlichungen sind keine voneinander unabhängigen Quellen.','Presseportal-Sammelfeeds enthalten auch andere Blaulichtorganisationen.','Bundesland bezeichnet die Einordnung im Dienststellenverzeichnis; Bundespolizei- und andere Dienststellen können länderübergreifend berichten.','Eine fehlgeschlagene Prüfung beweist nicht die Einstellung eines Feeds. Einige Presseportal-Abrufe lieferten vorübergehend HTTP 503.','Die Sammlung ist keine vollständige Liste aller deutschen Polizeidienststellen.','Keine aktive Feed-Auswahl geändert.']}
 (ROOT/'docs/police-feed-catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 opml=ET.Element('opml',version='2.0');head=ET.SubElement(opml,'head');ET.SubElement(head,'title').text='Polizei DE und AT – aktuelle bestätigte Feeds';body=ET.SubElement(opml,'body')
 for country,label in [('AT','Österreich'),('DE','Deutschland')]:
  group=ET.SubElement(body,'outline',text=label,title=label)
  for region in sorted({f['region'] for f in active if f['publisher_country']==country}):
   folder=ET.SubElement(group,'outline',text=region,title=region)
   for e in active:
    if e['publisher_country']==country and e['region']==region:ET.SubElement(folder,'outline',type='rss',text=e['name'],title=e['name'],xmlUrl=e['url'],htmlUrl=e['evidence_url'])
 ET.indent(opml);ET.ElementTree(opml).write(ROOT/'docs/police-feed-catalog.opml',encoding='utf-8',xml_declaration=True)
 def safe(s):return re.sub(r'\s+',' ',s).replace('|',' / ').replace('[','(').replace(']',')')
 lines=['# Polizei-RSS-Feeds: Deutschland und Österreich','',f'Stand: **{raw["researched_on"]}**. Direkter Abruf und XML-Prüfung, keine Aktivierung in der Sendung.','',f'**{len(feeds)} Polizeifeeds**, davon **{len(active)} mit Meldungen innerhalb von 14 Tagen**, {len(feeds)-len(active)} zur Aktualitätsprüfung. Zusätzlich {len(mixed)} gemischte Blaulicht-Sammelfeeds und {len(related)} verwandte österreichische Behördenfeeds. Atom-Darstellungen werden als Alternative vermerkt und nicht doppelt gezählt.','', '**Dateien:** [JSON-Katalog](../police-feed-catalog.json) · [OPML-Import](../police-feed-catalog.opml) · [Prüfprotokoll](../../research/police-rss/checks.json). Die OPML enthält ausschließlich aktuelle, bestätigte Polizeifeeds; keine Feuerwehr-, Zoll-, Gewerkschafts- oder gemischten Blaulichtfeeds.','', '## Österreich: alle neun Landespolizeidirektionen','','Das [offizielle BMI-Verzeichnis](https://www.bmi.gv.at/rss_feed/start.html) stellt die neun Landespolizeidirektionen jeweils als RSS und Atom bereit. Die zugehörigen RSS- und Atom-Adressen wurden geprüft; nur erfolgreich geladene RSS-Feeds werden unten ausgegeben.','','| Bundesland | RSS | Atom |','|---|---|---|']
 for e in feeds:
  if e['publisher_country']=='AT' and e['region']!='Österreich':lines.append(f'| {e["region"]} | [RSS]({e["url"]}) | [Atom]({e["atom_url"]}) |')
 lines+=['', 'Für die Sendung: LPD-Feeds können Meldungen ohne direkte Artikel-Links enthalten. In diesen Fällen ist `description` beziehungsweise Atom-`summary` die Textquelle. Die tatsächlich geprüfte Zahl vorhandener Artikel-Links, Textlängen und Meldungsdaten sind im JSON festgehalten.','', 'Weitere österreichische Quellen:']
 for e in feeds+related:
  if e['publisher_country']=='AT' and e['region']=='Österreich':lines.append(f'- [{e["name"]}]({e["url"]}) ({"Polizeiliche Bundesbehörde" if e in feeds else "verwandte Behörde, gesondert geführt"}).')
 lines+=['','## Deutschland: direkte Behördenfeeds','','| Behörde / Region | RSS | Aktualität |','|---|---|---|']
 for e in feeds:
  if e['publisher_country']=='DE' and e['source_type']=='authority':lines.append(f'| {e["name"]} / {e["region"]} | [Feed]({e["url"]}) | {"aktuell" if e["status"]=="verified_recent" else "Prüfung nötig"} |')
 lines+=['','[Polizei Bayern](https://www.polizei.bayern.de/aktuelles/001127/index.html), [Polizei Brandenburg](https://polizei.brandenburg.de/liste/die-neuesten-polizeimeldungen-auf-dem-sc/60761) und [Polizei Hessen](https://www.polizei.hessen.de/Startseite/) dokumentieren eigene RSS-Angebote. Ob ein auswertbares Meldungsdatum vorliegt, steht pro Feed im Katalog. Undatierte Nachrichtenfeeds werden zur Prüfung markiert.','', '## Deutschland: einzelne Polizeibehörden über Presseportal','','Ausgangspunkt ist das [Dienststellenverzeichnis](https://www.presseportal.de/blaulicht/dienststellen). Die Originalmitteilungen stammen von den jeweils genannten Behörden; technisch werden diese Feeds vom Presseportal ausgeliefert. Feuerwehr-, Rettungsdienst-, Zoll-, Gewerkschafts- und sonstige nichtpolizeiliche Feeds wurden anhand der Absenderbezeichnung ausgeschlossen. Überschneidungen mit Behörden-Webseiten sind möglich.','','| Bundesland / Einordnung | Polizeifeeds | Davon aktuell |','|---|---:|---:|']
 stations=[f for f in feeds if f['source_type']=='pressportal_station']
 for region in sorted({f['region'] for f in stations}):
  es=[f for f in stations if f['region']==region];lines.append(f'| {region} | {len(es)} | {sum(f["status"]=="verified_recent" for f in es)} |')
 lines+=['','| Einordnung | Behörde / Absender | RSS | Aktualität |','|---|---|---|---|']
 for e in stations:lines.append(f'| {e["region"]} | {safe(e["name"])} | [Feed]({e["url"]}) | {"aktuell" if e["status"]=="verified_recent" else "prüfen: "+str(e["newest_item_at"] or "undatiert")[:10]} |')
 lines+=['','## Gemischte Blaulichtfeeds – getrennt von Polizeifeeds','','Das [Presseportal-RSS-Verzeichnis](https://www.presseportal.de/rss/) bietet einen Gesamtfeed und Länderfeeds. Sie können auch Feuerwehr, Rettungsdienst oder andere Organisationen enthalten. Berlin und Brandenburg werden dort gemeinsam geführt.','','| Abdeckung | RSS |','|---|---|']
 for e in mixed:lines.append(f'| {e["region"]} | [Feed]({e["url"]}) |')
 lines+=['','## Grenzen und besondere Fälle','','- **Bundespolizei:** Zum ursprünglichen Recherchestand 2026-10-28 kündigte die [offizielle Presseseite](https://bundespolizei.de/presse/pressemitteilungen) den eigenen RSS-Feed als künftig wieder verfügbar an und verwies auf das Presseportal. Der Hinweis ersetzt keine erneute Prüfung der Webseite. Geprüfte Bundespolizei-Feeds über Presseportal sind oben enthalten.','- **Sachsen:** Die [offizielle Polizei-Seite](https://www.polizei.sachsen.de/de/presseinfo_aktuell.asp) nennt RSS über den Medienservice nach Registrierung. Ein frei zugänglicher landesweiter Behördenfeed wurde hier nicht bestätigt. Presseportal-Einträge aus Sachsen enthalten unter anderem Bundespolizei; das ist keine vollständige Abdeckung der sächsischen Landespolizei.','- **Vorübergehende Abruffehler:** Einzelne Presseportal-Adressen können vorübergehend HTTP 503 liefern. Diese wurden nicht als funktionierende Feeds ausgegeben. Daraus folgt keine dauerhafte Abschaltung oder ein fehlendes Angebot für das betreffende Bundesland.','- **14-Tage-Schwelle:** Ein älterer letzter Eintrag kann bei selten berichtenden Dienststellen normal sein. Solche Feeds stehen mit Prüfstatus im JSON, nicht in der OPML.','- **Quellenrolle:** Polizeipresse ist eine behördliche Darstellung. Dieselbe Meldung auf Behörden-Webseite und Presseportal ist keine unabhängige Gegenrecherche.','- **Geografie:** Die Bundesland-Einordnung kommt aus dem Presseportal-Verzeichnis. Einzelne Bundesbehörden und Bundespolizeidienststellen können auch über andere Länder berichten.','- **Nutzung:** Feed-Erreichbarkeit ist keine pauschale Lizenz für Artikel, Bilder oder personenbezogene Angaben. Die Quellenauswahl bleibt unverändert.','', 'Die Recherche ist mit den Skripten unter `research/police-rss/` reproduzierbar. Im Prüfprotokoll werden ausschließlich technische Kennwerte und Feed-Metadaten gespeichert, keine vollständigen Meldungstexte.','']
 (ROOT/'docs/guide/polizei-rss-quellenliste.md').write_text('\n'.join(lines))
 if (HERE/'emergency-checks.json').exists():
  from extend_catalog import extend_catalog
  extend_catalog(ROOT,HERE)
 else:
  print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
