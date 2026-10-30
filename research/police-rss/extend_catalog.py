#!/usr/bin/env python3
"""Extend the existing police catalogue, preserving the distinction between news and alerts."""
import collections
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

def extend_catalog(root,here):
 path=root/'docs/police-feed-catalog.json';data=json.loads(path.read_text())
 base=[e for e in data['feeds'] if e.get('category','Polizei')=='Polizei']
 for e in base:e.update(category='Polizei',sectors=['Polizei'],purpose='police_press',requires_warning_adapter=False)
 raw=json.loads((here/'checks.json').read_text());extra=json.loads((here/'emergency-checks.json').read_text());added=[];excluded=[];seen={e['url'] for e in base}
 def make(r,category,purpose,sectors=None):
  url=r.get('resolved_url',r['url'])
  if url in seen:return
  seen.add(url)
  name=r.get('name') or r.get('feed_title') or category
  title=r.get('feed_title','').removeprefix('Presseportal.de - ')
  # Directory names are more useful than generic titles for area-specific warnings.
  if purpose!='official_warning' and title:name=title
  notes=[];warning=purpose=='official_warning'
  if warning:
   status='available_empty' if r['status']=='empty' else 'verified_warning_feed'
   notes.append('Technisch geprüfter Warnfeed; Anzahl oder Datum der Einträge bestätigt keine aktuell gültige Gefahrenlage.')
   notes.append('Vor automatischer Sendungsverwendung Gültigkeit, Gebiet sowie Aktualisierungen und Entwarnungen auswerten.')
  else:
   status='verified_recent' if r.get('freshness')=='recent' else 'review'
   if status=='review':notes.append('Keine innerhalb von 14 Tagen datierte Meldung bestätigt; bei selten berichtenden Organisationen kein Abschaltungsnachweis.')
  if not url.startswith('https://'):status='review';notes.append('Weiterleitung auf HTTP.')
  if purpose=='organization_news':notes.append('Organisations- und Pressemeldungen; keine vollständige öffentliche Echtzeit-Einsatzliste.')
  if purpose=='incident_report':notes.append('Einsatz- und Presseberichte; eine Meldung ist keine aktuelle behördliche Warnung.')
  e={'id':hashlib.sha256(url.encode()).hexdigest()[:12],'publisher':title if r['source_type']=='pressportal_station' else r.get('name') or title,'name':name,'url':url,'language':'de','declared_language':r.get('declared_language',''),'publisher_country':r['country'],'region':r['region'],'category':category,'sectors':sectors or [category],'topic':category,'purpose':purpose,'suggested_section':'local','source_type':r['source_type'],'format':r['format'],'status':status,'checked_at':r['checked_at'],'newest_item_at':r.get('newest_item_at'),'item_count':r['item_count'],'evidence_url':r['evidence_url'],'notes':notes,'requires_warning_adapter':warning,'enabled_by_default':False}
  added.append(e)
 for r in raw['feeds']:
  if r['status']!='valid' or r['source_type']!='pressportal_station':continue
  title=r.get('feed_title','').casefold()
  if re.search(r'rettungsdienst|rotes kreuz|\bdrk\b|johanniter|malteser|samariter|\bdlrg\b|wasserwacht|bergwacht',title):
   make(r,'Rettungsdienst','incident_report',['Rettungsdienst','Feuerwehr'] if 'feuerwehr' in title else ['Rettungsdienst'])
  elif 'feuerwehr' in title:make(r,'Feuerwehr','incident_report')
  elif re.search(r'technisches hilfswerk|\bthw\b',title):make(r,'Katastrophenschutz','organization_news')
 for r in extra['feeds']:
  if r['status'] not in ('valid','empty'):continue
  if r['status']=='empty' and r['purpose']!='official_warning':continue
  if r['category']=='Landeswarnzentralen':
   excluded.append({'url':r['url'],'reason':'Nur allgemeiner Landesnachrichtenfeed; kein dedizierter Warn- oder Einsatzfeed der Landeswarnzentrale bestätigt.'});continue
  if any(s in r['url'].casefold() for s in ('uebungen','veranstaltungen','feuerwehr-hessen-tv')):
   excluded.append({'url':r['url'],'reason':'Übungs-, Termin- oder Videokanal statt Nachrichten-/Einsatzfeed'});continue
  make(r,r['category'],r['purpose'])
 feeds=base+sorted(added,key=lambda e:(e['category'],e['publisher_country'],e['region'],e['name']))
 eligible=[e for e in feeds if e['status'] in ('verified_recent','verified_warning_feed','available_empty') and e['url'].startswith('https://')]
 sources=[]
 for d in extra['directories']:
  matching=[e for e in added if e['evidence_url']==d['url']]
  is_center=d['category']=='Landeswarnzentralen'
  if matching and not is_center:continue
  sources.append({'name':d['name'],'url':d.get('resolved_url',d['url']),'publisher_country':d['country'],'region':d['region'],'category':d['category'],'purpose':d['purpose'],'format':'api_documentation' if 'data.hub.geosphere.at' in d['url'] else 'web','status':'no_dedicated_feed_confirmed' if d.get('reachable') else 'unverified','checked_at':d['checked_at'],'reachable':d.get('reachable',False),'integration_status':'additional_adapter_required','notes':['Webseite oder dokumentierte Schnittstelle; kein direkt importierbarer spezifischer RSS-/Atom-Feed bestätigt.'],'enabled_by_default':False})
 data['excluded']=[e for e in data.get('excluded',[]) if e['url'] not in seen]
 data.update(schema_version=2,title='Polizei, Feuerwehr, Rettungsdienst und öffentliche Warnquellen DE/AT',feeds=feeds,non_feed_sources=sources,extension_excluded=excluded)
 data['counts'].update(total_feeds=len(feeds),additional_emergency_feeds=len(added),importable_feeds=len(eligible),feeds_by_category=dict(collections.Counter(e['category'] for e in feeds)),non_feed_sources=len(sources),warning_feeds=sum(e['purpose']=='official_warning' for e in feeds),empty_warning_feeds=sum(e['status']=='available_empty' for e in feeds))
 data['counts']['additional_candidates_checked']=len(extra['feeds'])
 data['limitations']=[s for s in data.get('limitations',[]) if 'Warnfeed' not in s and not s.startswith('Landeswarnzentralen und Web-/API-Quellen')]+['Warnfeeds sind keine Einsatzberichte. Leere Warnfeeds können regulär sein; weder ein leeres Ergebnis noch ein alter Eintrag bestätigt Entwarnung.','CAP-/Warnfeeds benötigen vor automatischer Sendungsverwendung die Prüfung von Status, Gebiet, Gültigkeit, Updates und Cancel/Entwarnung.','Landeswarnzentralen und Web-/API-Quellen ohne bestätigten spezifischen Feed sind getrennt dokumentiert und nicht als RSS importierbar.']
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 opml=ET.Element('opml',version='2.0');head=ET.SubElement(opml,'head');ET.SubElement(head,'title').text=data['title'];body=ET.SubElement(opml,'body')
 for category in sorted({e['category'] for e in eligible}):
  group=ET.SubElement(body,'outline',text=category,title=category)
  for country in ('AT','DE'):
   entries=[e for e in eligible if e['category']==category and e['publisher_country']==country]
   if not entries:continue
   folder=ET.SubElement(group,'outline',text='Österreich' if country=='AT' else 'Deutschland')
   for e in entries:ET.SubElement(folder,'outline',type='rss',text=e['name'],title=e['name'],xmlUrl=e['url'],htmlUrl=e['evidence_url'])
 ET.indent(opml);ET.ElementTree(opml).write(root/'docs/police-feed-catalog.opml',encoding='utf-8',xml_declaration=True)
 doc=root/'docs/guide/polizei-rss-quellenliste.md';old=doc.read_text().split('\n<!-- emergency-extension -->')[0]
 old=old.replace('# Polizei-RSS-Feeds: Deutschland und Österreich','# Polizei, Feuerwehr, Rettungsdienst und Warnquellen: DE / AT',1)
 old=old.replace('Die OPML enthält ausschließlich aktuelle, bestätigte Polizeifeeds; keine Feuerwehr-, Zoll-, Gewerkschafts- oder gemischten Blaulichtfeeds.','Die OPML enthält aktuelle bestätigte Nachrichtenfeeds sowie technisch verfügbare Warnfeeds, nach Kategorien gruppiert. Gemischte Blaulicht-Sammelfeeds bleiben gesondert. Leere Warnfeeds können regulär sein. Web-/API-Quellen ohne Feed werden nicht importiert.')
 old=old.replace('Feuerwehr-, Rettungsdienst-, Zoll-, Gewerkschafts- und sonstige nichtpolizeiliche Feeds wurden anhand der Absenderbezeichnung ausgeschlossen.','Feuerwehr- und Rettungsdienst-Feeds sind in den zusätzlichen Kategorien am Ende dieser Liste enthalten; Zoll-, Gewerkschafts- und sonstige fachfremde Feeds bleiben ausgeschlossen.')
 summary=f'\n\n**Erweiterter Katalog:** {len(feeds)} RSS-/Atom-Feeds, davon {len(added)} zusätzlich aus Feuerwehr, Rettungsdienst, Katastrophenschutz und Warnsystemen. {len(sources)} weitere Web-/API-Quellen sind separat dokumentiert. Siehe die [Erweiterung am Ende](#erweiterung-feuerwehr-rettungsdienst-und-warnungen).'
 # Rebuilding from the base generator is supported; standalone runs are idempotent too.
 old=re.sub(r'\n\n\*\*Erweiterter Katalog:\*\*.*?(?=\n\n)', '',old,count=1,flags=re.S)
 pos=old.index('\n\n');old=old[:pos]+summary+old[pos:]
 def safe(s):return re.sub(r'\s+',' ',s).replace('|',' / ').replace('[','(').replace(']',')')
 lines=['','<!-- emergency-extension -->','', '## Erweiterung: Feuerwehr, Rettungsdienst und Warnungen','', '| Kategorie | Feeds gesamt | Im OPML-Import |','|---|---:|---:|']
 for category in sorted({e['category'] for e in added}):lines.append(f'| {category} | {sum(e["category"]==category for e in added)} | {sum(e["category"]==category for e in eligible if e not in base)} |')
 lines+=['', 'Die Feuerwehr- und THW-Feeds des [Presseportal-Dienststellenverzeichnisses](https://www.presseportal.de/blaulicht/dienststellen) wurden aus dem bereits gespeicherten Prüfprotokoll übernommen. Neue Organisations- und Warnquellen wurden direkt geladen und auf gültiges RSS/Atom geprüft. Organisationsmeldungen von Rettungsdiensten können auch Ausbildung, Verbandspolitik oder humanitäre Hilfe betreffen; sie sind kein öffentliches vollständiges Rettungseinsatzprotokoll.','', '### Warnfeeds: andere Bedeutung als Einsatznachrichten','', 'Amtliche Warnungen enthalten Gültigkeitszeiträume, betroffene Gebiete und gegebenenfalls Aktualisierungen oder Entwarnungen. Ein technisch lesbarer Feed mit Einträgen beweist keine aktuell gültige Warnung. Ein leerer Warnfeed ist nicht automatisch defekt; daraus allein wird auch keine Entwarnung abgeleitet. Für die Sendung ist ein zusätzlicher Warnungsadapter erforderlich, der diese Angaben auswertet. Es wurde kein Warnsystem aktiviert.','', 'Geprüfte Quellen sind unter anderem die [DWD CAP-Feeds](https://www.dwd.de/DE/leistungen/opendata/help/warnungen/dwd_warnings_products_overview_en_pdf.pdf?__blob=publicationFile&v=3), [MeteoAlarm](https://api.meteoalarm.org/) für Österreich und Deutschland, das [Hochwasserportal](https://www.hochwasserzentralen.de/) sowie ortsbezogene BBK-/MoWaS-RSS-Feeds. Das [BBK beschreibt RSS für die Ortsauswahl](https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warn-App-NINA/warn-app-nina_node.html). Berlin, Hamburg und München werden als Beispiel-Adressen geprüft; nur technisch bestätigte Feeds erscheinen unten. Sie decken nicht ganz Deutschland ab.','', '| Kategorie | Land / Region | Organisation / Kanal | Feed | Prüfung |','|---|---|---|---|---|']
 for e in added:
  state='leer, technisch lesbar' if e['status']=='available_empty' else 'Warnfeed technisch lesbar' if e['purpose']=='official_warning' else 'aktuell' if e['status']=='verified_recent' else 'Aktualität prüfen'
  lines.append(f'| {e["category"]} | {e["publisher_country"]} / {e["region"]} | {safe(e["name"])} | [RSS/Atom]({e["url"]}) | {state} |')
 lines+=['', '### Landeswarnzentralen und zusätzliche Web-/API-Quellen','', 'Die österreichischen Landeswarn-/Lagezentralen und Warnsysteme sind mit ihren offiziellen Fundstellen erfasst. Wo kein spezifischer öffentlicher RSS-/Atom-Feed bestätigt wurde, steht ausdrücklich „zusätzliche Anbindung nötig“. Allgemeine Landesnachrichtenfeeds werden nicht als Warnfeed ausgegeben.','', 'AT-Alert ist die öffentliche behördliche Warnseite der [RTR](https://www.rtr.at/rtr/service/at_alert/at_alert_startseite.de.html). [GeoSphere](https://data.hub.geosphere.at/dataset/warnungen-v1) dokumentiert eine Wetterwarnungs-API. Diese Quellen werden nicht als RSS-Adressen ausgegeben. Öffentliche Einsatzübersichten etwa der LSZ Burgenland oder LAWZ Kärnten sind außerdem keine vollständigen Echtzeitwarnungen. Die [Nutzungshinweise der LAWZ Kärnten](https://alarmierungen.feuerwehr-ktn.at/termsOfUse.html) erläutern Verzögerungen und die Abgrenzung zu amtlichen Warnungen.','', '| Bereich | Land / Region | Quelle | Technischer Stand |','|---|---|---|---|']
 for e in sources:lines.append(f'| {e["category"]} | {e["publisher_country"]} / {e["region"]} | [{safe(e["name"])}]({e["url"]}) | {"Web/API; zusätzliche Anbindung nötig" if e["reachable"] else "Abruf nicht bestätigt; prüfen"} |')
 lines+=['', 'Zusätzliche technische Ergebnisse: [emergency-checks.json](../../research/police-rss/emergency-checks.json). Die bereits zuvor dokumentierten Polizeifeeds und ihre Prüfdaten bleiben erhalten. Die aktive Sendungskonfiguration wurde nicht geändert.','']
 doc.write_text(old.rstrip()+'\n'+'\n'.join(lines))
 print(json.dumps(data['counts'],ensure_ascii=False))

if __name__=='__main__':
 here=Path(__file__).resolve().parent
 extend_catalog(here.parents[1],here)
