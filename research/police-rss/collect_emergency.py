#!/usr/bin/env python3
"""Discover public fire/rescue news and warning feeds; keep web-only sources explicit."""
import concurrent.futures as cf
import datetime as dt
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import re
import urllib.parse
from discover import read,Links
from collect import probe
OUT=Path(__file__).resolve().parent
# name, country, region, category, publication purpose, official site, explicit candidates
SEEDS=[
('Landessicherheitszentrale Burgenland','AT','Burgenland','Landeswarnzentralen','portal','https://www.lsz-b.at/',[]),
('LSZ Burgenland – Einsatzübersicht','AT','Burgenland','Landeswarnzentralen','incident_status','https://einsatz.lsz-b.at/',[]),
('Landeswarnzentrale Niederösterreich','AT','Niederösterreich','Landeswarnzentralen','portal','https://www.noel.gv.at/noe/Katastrophenschutz/Landeswarnzentrale.html',[]),
('Landeswarnzentrale Oberösterreich','AT','Oberösterreich','Landeswarnzentralen','portal','https://www.ooelfv.at/das-kommando/standorte/ooe-landeswarnzentrale',[]),
('Landesalarm- und Warnzentrale Kärnten','AT','Kärnten','Landeswarnzentralen','portal','https://www.feuerwehr-ktn.at/verband/lawz/',[]),
('LAWZ Kärnten – öffentliche Einsatzübersicht','AT','Kärnten','Landeswarnzentralen','incident_status','https://alarmierungen.feuerwehr-ktn.at/',[]),
('Landeswarnzentrale Steiermark','AT','Steiermark','Landeswarnzentralen','portal','https://www.verwaltung.steiermark.at/cms/ziel/75757731/DE/',[]),
('Landesalarm- und Warnzentrale Salzburg','AT','Salzburg','Landeswarnzentralen','portal','https://www.salzburg.gv.at/themen/sicherheit/katastrophenschutz',[]),
('Landes-Warn- und Lagezentrum Tirol','AT','Tirol','Landeswarnzentralen','portal','https://www.tirol.gv.at/sicherheit/kkm/krisen-und-gefahrenmanagement/landes-warn-und-lagezentrum/erreichbarkeit-und-dienstbetrieb/',[]),
('Landeswarnzentrale Vorarlberg','AT','Vorarlberg','Landeswarnzentralen','portal','https://vorarlberg.at/-/landeswarnzentrale',[]),
('Warndienste Vorarlberg','AT','Vorarlberg','Landeswarnzentralen','official_warning','https://warnung.vorarlberg.at/vtgdb/dist/index.html',[]),
('Wien – Warn- und Alarmsystem / Krisenmanagement','AT','Wien','Landeswarnzentralen','portal','https://www.wien.gv.at/zusammenleben/sirenen-probealarme',[]),
('AT-Alert – behördliche Warnungen','AT','Österreich','Warnungen','official_warning','https://warnung.at-alert.at/de',[]),
('GeoSphere Austria – Wetterwarnungen','AT','Österreich','Wetter / Naturgefahren','official_warning','https://data.hub.geosphere.at/dataset/warnungen-v1',[]),
('MeteoAlarm Österreich','AT','Österreich','Wetter / Naturgefahren','official_warning','https://api.meteoalarm.org/',['https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-austria']),
('MeteoAlarm Deutschland','DE','Deutschland','Wetter / Naturgefahren','official_warning','https://api.meteoalarm.org/',['https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-germany']),
('DWD – amtliche Wetterwarnungen','DE','Deutschland','Wetter / Naturgefahren','official_warning','https://www.dwd.de/DE/leistungen/opendata/help/warnungen/dwd_warnings_products_overview_en_pdf.pdf?__blob=publicationFile&v=3',['https://www.dwd.de/DWD/warnungen/cap-feed/de/rss.xml']),
('BBK / NINA / MoWaS – Berlin','DE','Berlin','Warnungen','official_warning','https://warnung.bund.de/',['https://warnung.bund.de/api31/mowas/rss/110000000000.rss']),
('BBK / NINA / MoWaS – Hamburg','DE','Hamburg','Warnungen','official_warning','https://warnung.bund.de/',['https://warnung.bund.de/api31/mowas/rss/020000000000.rss']),
('BBK / NINA / MoWaS – München','DE','Bayern','Warnungen','official_warning','https://warnung.bund.de/',['https://warnung.bund.de/api31/mowas/rss/091620000000.rss']),
('Länderübergreifendes Hochwasserportal','DE','Deutschland','Wetter / Naturgefahren','official_warning','https://www.hochwasserzentralen.de/',[]),
('Lawinenwarndienste Österreich','AT','Österreich','Wetter / Naturgefahren','official_warning','https://www.lawinen.at/',[]),
('Europaregion – Lawinenbericht','AT','Tirol','Wetter / Naturgefahren','official_warning','https://avalanche.report/',[]),
('Österreichischer Bundesfeuerwehrverband','AT','Österreich','Feuerwehr','organization_news','https://www.bundesfeuerwehrverband.at/',['https://www.bundesfeuerwehrverband.at/feed/']),
('LFV Steiermark','AT','Steiermark','Feuerwehr','organization_news','https://www.lfv.steiermark.at/',[]),
('LFV Oberösterreich','AT','Oberösterreich','Feuerwehr','organization_news','https://www.ooelfv.at/',[]),
('NÖ Landesfeuerwehrverband','AT','Niederösterreich','Feuerwehr','organization_news','https://www.noe122.at/',[]),
('LFV Tirol','AT','Tirol','Feuerwehr','organization_news','https://www.lfv-tirol.at/',[]),
('LFV Kärnten','AT','Kärnten','Feuerwehr','organization_news','https://www.feuerwehr-ktn.at/',[]),
('LFV Vorarlberg','AT','Vorarlberg','Feuerwehr','organization_news','https://www.lfv-vorarlberg.at/',[]),
('LFV Salzburg','AT','Salzburg','Feuerwehr','organization_news','https://www.lfv-sbg.at/',[]),
('LFV Burgenland','AT','Burgenland','Feuerwehr','organization_news','https://www.lfv-bgld.at/',[]),
('Feuerwehr Neutal','AT','Burgenland','Feuerwehr','organization_news','https://www.feuerwehr-neutal.at/',['https://www.feuerwehr-neutal.at/feed/']),
('Österreichisches Rotes Kreuz','AT','Österreich','Rettungsdienst','organization_news','https://www.roteskreuz.at/',[]),
('Samariterbund Österreich','AT','Österreich','Rettungsdienst','organization_news','https://www.samariterbund.net/',[]),
('Johanniter Österreich','AT','Österreich','Rettungsdienst','organization_news','https://www.johanniter.at/',[]),
('Österreichischer Bergrettungsdienst','AT','Österreich','Rettungsdienst','organization_news','https://bergrettung.at/',['https://bergrettung.at/feed/']),
('Bergrettung Steiermark','AT','Steiermark','Rettungsdienst','organization_news','https://www.bergrettung-stmk.at/',[]),
('Österreichische Wasserrettung','AT','Österreich','Rettungsdienst','organization_news','https://www.owr.at/',['https://www.owr.at/feed/']),
('Deutsches Rotes Kreuz','DE','Deutschland','Rettungsdienst','organization_news','https://www.drk.de/presse/',['https://www.drk.de/news-rss.xml','https://www.presseportal.de/rss/pm_66641.rss2']),
('DRK Sachsen-Anhalt','DE','Sachsen-Anhalt','Rettungsdienst','organization_news','https://www.sachsen-anhalt.drk.de/footer-menue-deutsch/service/sitemap.html',[]),
('Johanniter-Unfall-Hilfe','DE','Deutschland','Rettungsdienst','organization_news','https://www.johanniter.de/presse/',['https://www.presseportal.de/rss/pm_14240.rss2']),
('Malteser Hilfsdienst','DE','Deutschland','Rettungsdienst','organization_news','https://www.malteser.de/',['https://www.presseportal.de/rss/pm_51360.rss2']),
('Arbeiter-Samariter-Bund','DE','Deutschland','Rettungsdienst','organization_news','https://www.asb.de/',[]),
('DLRG','DE','Deutschland','Rettungsdienst','organization_news','https://www.dlrg.de/informieren/die-dlrg/presse/',[]),
('DLRG Schleswig-Holstein','DE','Schleswig-Holstein','Rettungsdienst','organization_news','https://schleswig-holstein.dlrg.de/nachrichten/nachrichtenarchiv/',[]),
('Deutscher Feuerwehrverband','DE','Deutschland','Feuerwehr','organization_news','https://www.feuerwehrverband.de/',['https://www.feuerwehrverband.de/feed/']),
('Landesfeuerwehrverband Hessen','DE','Hessen','Feuerwehr','organization_news','https://www.feuerwehr-hessen.de/informiert-bleiben',[]),
('Berliner Feuerwehr','DE','Berlin','Feuerwehr','incident_report','https://www.berliner-feuerwehr.de/service/rss-feeds/',[]),
('Technisches Hilfswerk','DE','Deutschland','Katastrophenschutz','organization_news','https://www.thw.de/',[]),
]
PRESS=[('Deutsches Rotes Kreuz',66641),('Johanniter-Unfall-Hilfe',14240),('Malteser Hilfsdienst',51360)]

def discover(seed):
 name,country,region,category,purpose,page,explicit=seed
 base=dict(name=name,country=country,region=region,category=category,purpose=purpose,source_type='authority' if purpose=='official_warning' or category=='Landeswarnzentralen' else 'organization',evidence_url=page,language='de')
 candidates=[dict(base,url=u,discovery='curated_candidate') for u in explicit]
 record=dict(base,url=page,checked_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
 try:
  final,b=read(page);record['resolved_url']=final;record['reachable']=True
  if not page.lower().endswith('.pdf') and b.lstrip()[:4]!=b'%PDF':
   p=Links();p.feed(b.decode('utf-8',errors='replace'))
   for path,label in p.rows:
    u=urllib.parse.urljoin(final,path)
    if u.startswith('http://'):u='https://'+u[7:]
    if not re.search(r'(?:[/_~?=.-](?:rss|atom|feed)(?:\b|[_.?/]))|(?:\.rss|\.rdf|\.xml)' ,u,re.I):continue
    if not u.startswith('https://') or any(t in u.lower() for t in ('comments','comment/feed','podcast','jobs','karriere')):continue
    if urllib.parse.urlparse(u).netloc.split('.')[-2:] != urllib.parse.urlparse(final).netloc.split('.')[-2:]:continue
    candidates.append(dict(base,url=u,discovery='publisher_link',link_label=label))
  record['feed_candidate_count']=len(candidates)
 except Exception as e:record.update(reachable=False,error=str(e)[:180])
 return candidates,record

def main():
 with cf.ThreadPoolExecutor(max_workers=4) as pool:found=list(pool.map(discover,SEEDS))
 candidates=[];seen=set()
 for rows,_ in found:
  for r in rows[:10]:
   if r['url'] not in seen:seen.add(r['url']);candidates.append(r)
 # Read original newsrooms to obtain their actual publisher-linked RSS addresses.
 for name,number in PRESS:
  site=f'https://www.presseportal.de/nr/{number}'
  try:
   _,b=read(site);p=Links();p.feed(b.decode('utf-8',errors='replace'))
   u=next((urllib.parse.urljoin(site,u) for u,label in p.rows if '/rss/' in u and f'pm_{number}' in u),'')
   if not u:u=next((urllib.parse.urljoin(site,u) for u,label in p.rows if '/rss/' in u),'')
   if u and u not in seen:
    seen.add(u);candidates.append(dict(name=name,country='DE',region='Deutschland',category='Rettungsdienst',purpose='organization_news',source_type='pressportal_organization',evidence_url=site,url=u,language='de',discovery='publisher_link'))
  except Exception:pass
 print('Checking',len(candidates),'additional feed candidates',flush=True)
 for r in candidates:
  if r['url']=='https://www.drk.de/news-rss.xml':r['read_limit_bytes']=8_000_000
 with cf.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(probe,candidates))
 data={'researched_on':dt.datetime.now(ZoneInfo('Europe/Vienna')).date().isoformat(),'directories':[r for _,r in found],'feeds':results}
 (OUT/'emergency-checks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print('Readable RSS/Atom:',sum(r['status'] in ('valid','empty') for r in results))
if __name__=='__main__':main()
