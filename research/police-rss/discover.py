import concurrent.futures as cf
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
import urllib.parse
OUT=Path(__file__).resolve().parent
PAGES={
'BMI Österreich':'https://www.bmi.gv.at/rss_feed/start.html',
'Polizei Bayern':'https://www.polizei.bayern.de/aktuelles/001127/index.html',
'Polizei Berlin':'https://www.berlin.de/polizei/polizeimeldungen/',
'Polizei Brandenburg':'https://polizei.brandenburg.de/liste/die-neuesten-polizeimeldungen-auf-dem-sc/60761',
'Polizei Hessen':'https://www.polizei.hessen.de/Startseite/',
'Polizei Sachsen':'https://www.polizei.sachsen.de/de/presseinfo_aktuell.asp',
'Bundespolizei':'https://bundespolizei.de/presse/pressemitteilungen',
'BKA Deutschland':'https://www.bka.de/DE/Presse/presse_node.html',
'Polizei NRW':'https://polizei.nrw/presse',
'Presseportal Verzeichnis':'https://www.presseportal.de/rss/',
'Presseportal Blaulicht':'https://www.presseportal.de/blaulicht/',
'Presseportal Dienststellen':'https://www.presseportal.de/blaulicht/dienststellen',
}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.a=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a':self.a=[a.get('href',''),'']
  if tag=='link' and ('rss' in a.get('type','') or 'atom' in a.get('type','')):self.rows.append([a.get('href',''),a.get('title','')])
 def handle_data(self,data):
  if self.a:self.a[1]+=data
 def handle_endtag(self,tag):
  if tag=='a' and self.a:self.rows.append(self.a);self.a=None

def read(u,max_bytes=2_000_000):
 req=urllib.request.Request(u,headers={'User-Agent':'PersonalNewsHost police RSS research/1.0'})
 with urllib.request.urlopen(req,timeout=15) as r:return r.geturl(),r.read(max_bytes)

def discover(pair):
 name,u=pair
 try:
  final,b=read(u);p=Links();p.feed(b.decode('utf-8',errors='replace'));links=[]
  for path,label in p.rows:
   path=urllib.parse.urljoin(final,path)
   if re.search(r'rss|feed|blaulicht/(?:nr|dienststellen)|presseportal.de',path,re.I):links.append({'url':path,'label':' '.join(label.split())[:160]})
  return {'name':name,'url':u,'resolved_url':final,'links':links}
 except Exception as e:return {'name':name,'url':u,'error':str(e)}
if __name__=='__main__':
 with cf.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(discover,PAGES.items()))
 (OUT/'discovery.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 for r in rows:print(r['name'],r.get('error',''),json.dumps(r.get('links',[])[:30],ensure_ascii=False))
