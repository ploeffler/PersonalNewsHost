#!/usr/bin/env python3
"""Research public Austrian and German police feeds with direct XML validation."""
import concurrent.futures as cf
import datetime as dt
from zoneinfo import ZoneInfo
import email.utils
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import statistics
import time
import urllib.parse
import xml.etree.ElementTree as ET
from discover import read,Links
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
AT={'bgld':'Burgenland','ktn':'Kärnten','noe':'Niederösterreich','ooe':'Oberösterreich','sbg':'Salzburg','stmk':'Steiermark','tirol':'Tirol','vbg':'Vorarlberg','wien':'Wien'}

class Stations(HTMLParser):
 def __init__(self):super().__init__();self.heading=None;self.region='Deutschland';self.rows=[];self.a=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h3':self.heading=''
  if tag=='a' and re.search(r'/blaulicht/nr/\d+',a.get('href','')):self.a=[a['href'],'',self.region]
 def handle_data(self,d):
  if self.heading is not None:self.heading+=d
  if self.a:self.a[1]+=d
 def handle_endtag(self,tag):
  if tag=='h3' and self.heading is not None:self.region=' '.join(self.heading.split());self.heading=None
  if tag=='a' and self.a:self.rows.append(self.a);self.a=None

def local(t):return t.rsplit('}',1)[-1]
def txt(n,tag):return next((' '.join(''.join(c.itertext()).split()) for c in n if local(c.tag)==tag),'')
def date(v):
 try:d=email.utils.parsedate_to_datetime(v)
 except (ValueError,TypeError,OverflowError):
  try:d=dt.datetime.fromisoformat(v.replace('Z','+00:00'))
  except (ValueError,TypeError):return None
 return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)
def probe(row):
 if 'presseportal.de' in row['url']:time.sleep(0.25)
 r=dict(row);r['checked_at']=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
 try:
  final,b=read(r['url'],r.get('read_limit_bytes',2_000_000));r['resolved_url']=final;root=ET.fromstring(b)
  if local(root.tag) not in ('rss','RDF','feed'):raise ValueError('No RSS/Atom/RDF root')
  channel=next((x for x in root if local(x.tag)=='channel'),root)
  entries=[x for x in root.iter() if local(x.tag) in ('item','entry')]
  title=txt(channel,'title');dates=[];lengths=[];links=0
  for entry in entries:
   v=txt(entry,'pubDate') or txt(entry,'published') or txt(entry,'updated') or txt(entry,'date');d=date(v)
   if d:dates.append(d)
   content=txt(entry,'description') or txt(entry,'summary') or txt(entry,'content')
   lengths.append(len(re.sub('<[^>]+>',' ',content)))
   link=next((c.get('href') or c.text or '' for c in entry if local(c.tag)=='link' and c.get('rel','alternate')=='alternate'),'')
   if link.startswith(('http://','https://')):links+=1
  newest=max(dates) if dates else None
  age=(dt.datetime.now(dt.timezone.utc)-newest).total_seconds()/86400 if newest else None
  r.update(feed_title=title,format='atom' if local(root.tag)=='feed' else 'rss1' if local(root.tag)=='RDF' else 'rss2',declared_language=txt(channel,'language') or root.get('{http://www.w3.org/XML/1998/namespace}lang',''),item_count=len(entries),newest_item_at=newest.isoformat() if newest else None,items_with_article_link=links,median_summary_chars=int(statistics.median(lengths)) if lengths else 0,status='valid' if entries else 'empty',freshness='undated' if age is None else 'future_date' if age< -2 else 'recent' if age<=14 else 'stale')
 except Exception as e:r.update(status='unavailable',error=str(e)[:200])
 return r

def main():
 discovery=json.loads((OUT/'discovery.json').read_text());rows=[]
 def add(name,url,country,region,kind,evidence,**kw):
  if url.startswith('http://'):url='https://'+url[7:]
  if not any(r['url']==url for r in rows):rows.append(dict(name=name,url=url,country=country,region=region,source_type=kind,evidence_url=evidence,language='de',suggested_section='local',**kw))
 for code,region in AT.items():
  add('LPD '+region,f'https://www.bmi.gv.at/rss/{code}_presse.xml','AT',region,'authority','https://www.bmi.gv.at/rss_feed/start.html',atom_url=f'https://www.bmi.gv.at/rss/{code}_pressea.xml')
 for code,label in [('bk','Bundeskriminalamt Österreich'),('bak','Bundesamt zur Korruptionsprävention und Korruptionsbekämpfung'),('bmi','BMI Österreich – Aktuelles')]:
  add(label,f'https://www.bmi.gv.at/rss/{code}_presse.xml','AT','Österreich','authority_related' if code!='bk' else 'authority','https://www.bmi.gv.at/rss_feed/start.html',atom_url=f'https://www.bmi.gv.at/rss/{code}_pressea.xml')
 for source in discovery:
  for l in source.get('links',[]):
   u=l['url']
   if source['name']=='Polizei Berlin' and '/rss' in u:add('Polizei Berlin',u,'DE','Berlin','authority',source['url'])
   if source['name']=='Polizei Brandenburg' and urllib.parse.urlparse(u).path in ('/pressemeldungen/rss','/rss'):add('Polizei Brandenburg',u,'DE','Brandenburg','authority',source['url'])
   if source['name']=='Polizei Hessen' and 'presse-feed' in u:add('Polizei Hessen',u,'DE','Hessen','authority',source['url'])
   if source['name']=='Presseportal Verzeichnis' and ('/rss/polizei' in u):add(l['label'] or 'Blaulicht-Sammelfeed',u,'DE','Deutschland','pressportal_mixed',source['url'])
 add('Polizei Bayern – aktuelle Mitteilungen','https://www.polizei.bayern.de/rss_aktuelle_mitteilungen.xml','DE','Bayern','authority','https://www.polizei.bayern.de/aktuelles/001127/index.html')
 # Official district sites may expose their own feed separate from Presseportal.
 for name,site in [('Polizei Duisburg','https://duisburg.polizei.nrw/'),('Polizei Köln','https://koeln.polizei.nrw/'),('Polizei Düsseldorf','https://duesseldorf.polizei.nrw/'),('Polizei Dortmund','https://dortmund.polizei.nrw/')]:
  try:
   final,b=read(site);p=Links();p.feed(b.decode('utf-8',errors='replace'))
   for u,label in p.rows:
    if re.search(r'/rss(?:[/.?]|$)|\.rss|\.xml',u):add(name,urllib.parse.urljoin(final,u),'DE','Nordrhein-Westfalen','authority',site)
  except Exception:pass
 site='https://www.presseportal.de/blaulicht/dienststellen';_,b=read(site);p=Stations();p.feed(b.decode('utf-8',errors='replace'))
 for path,label,region in p.rows:
  match=re.search(r'/nr/(\d+)',path)
  if match:
   number=match[1];add(label or 'Dienststelle '+number,f'https://www.presseportal.de/rss/dienststelle_{number}.rss2','DE',region,'pressportal_station',urllib.parse.urljoin(site,path),discovery_method='RSS address template verified against official Presseportal newsroom 6337')
 print('Checking',len(rows),'candidates',flush=True)
 with cf.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(probe,rows))
 # Atom variants are recorded and checked separately rather than counted twice.
 variants=[dict(r,url=r['atom_url'],variant_of=r['url']) for r in rows if r.get('atom_url')]
 with cf.ThreadPoolExecutor(max_workers=4) as pool:atoms=list(pool.map(probe,variants))
 data={'researched_on':dt.datetime.now(ZoneInfo('Europe/Vienna')).date().isoformat(),'method':'Official agency directories, HTML feed discovery and the Presseportal agency directory. Presseportal newsroom RSS template checked on original station page, each candidate then parsed directly. No personal article content retained.','feeds':results,'atom_variants':atoms}
 (OUT/'checks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'checked':len(rows),'valid':sum(r['status']=='valid' for r in results),'police_stations':sum(r['status']=='valid' and bool(re.search('polizei|police|kriminalamt',r.get('feed_title',''),re.I)) for r in results)},ensure_ascii=False))
if __name__=='__main__':main()
