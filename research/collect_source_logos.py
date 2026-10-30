#!/usr/bin/env python3
"""Refresh publisher favicons locally. Pillow validates downloaded raster images."""
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_ASSETS=ROOT/'docs/assets/source-logos'
CATALOGUES={'news':'feed-catalog.json','authorities':'police-feed-catalog.json'}
ALIASES={'feeds.bbci.co.uk':'www.bbc.com','rss.orf.at':'orf.at','rss.dw.com':'www.dw.com','rss.nytimes.com':'www.nytimes.com','feeds.npr.org':'www.npr.org','rss.sueddeutsche.de':'www.sueddeutsche.de','newsfeed.zeit.de':'www.zeit.de','rss.golem.de':'www.golem.de','api.krone.at':'www.krone.at','moxie.foxnews.com':'www.foxnews.com','feeds.skynews.com':'news.sky.com','feeds.nbcnews.com':'www.nbcnews.com','feeds.washingtonpost.com':'www.washingtonpost.com'}
ASSET=re.compile(r'^assets/source-logos/[a-f0-9]+\.(?:png|ico|jpg|gif|webp)$')

class Icons(HTMLParser):
    def __init__(self):super().__init__();self.icons=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and 'icon' in a.get('rel','').lower() and a.get('href'):
            self.icons.append(a['href'])

def fetch(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsHost source favicon cache/1.1'})
    with urllib.request.urlopen(req,timeout=10) as response:
        data=response.read(limit+1)
        if len(data)>limit:raise ValueError('Response too large')
        return response.geturl(),data

def download_icon(pair):
    host,site=pair
    candidates=[]
    try:
        final,body=fetch(site,2_000_000)
        parser=Icons();parser.feed(body.decode('utf-8',errors='replace'))
        candidates=[urllib.parse.urljoin(final,u) for u in parser.icons if not u.startswith('data:')]
        candidates.sort(key=lambda u:('.svg' in u.lower(),'.ico' in u.lower()))
    except Exception:pass
    for url in list(dict.fromkeys(candidates+[urllib.parse.urljoin(site,'/favicon.ico')]))[:4]:
        try:
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!='https' or parsed.username or parsed.password:continue
            final,body=fetch(url,350_000)
            with Image.open(io.BytesIO(body)) as image:
                if image.width>2048 or image.height>2048:continue
                fmt=image.format;image.verify()
            extension={'PNG':'png','ICO':'ico','JPEG':'jpg','GIF':'gif','WEBP':'webp'}.get(fmt)
            if extension:return {'source':final,'extension':extension,'data':body}
        except Exception:continue
    return None

def domains(root,groups):
    result={}
    for group in groups:
        data=json.loads((root/'docs'/CATALOGUES[group]).read_text())
        for key in ('feeds','mixed_feeds','related_authority_feeds','non_feed_sources'):
            for entry in data.get(key,[]):
                for field in ('url','source_page','evidence_url'):
                    parsed=urllib.parse.urlparse(entry.get(field,''))
                    if parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password:
                        result[parsed.hostname]='https://'+ALIASES.get(parsed.hostname,parsed.hostname)+'/'
    return result

def cached_bytes(row,cache_dir):
    if row.get('status')!='cached' or not ASSET.fullmatch(row.get('icon','')):return None
    try:
        body=(cache_dir/Path(row['icon']).name).read_bytes()
        return body if len(body)<=350_000 else None
    except OSError:return None

def fresh(row,today,days):
    try:age=(today-dt.date.fromisoformat(row['checked_on'])).days
    except (KeyError,ValueError,TypeError):return False
    return 0<=age<days

def atomic_write(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp')
    temp.write_bytes(body);temp.replace(path)

def refresh_logos(catalog_root=ROOT,output_dir=DEFAULT_ASSETS,cache_dir=DEFAULT_ASSETS,groups=('news','authorities'),refresh_days=30,today=None):
    if not 0<=refresh_days<=365:raise ValueError('refresh_days must be between 0 and 365')
    today=today or dt.datetime.now(ZoneInfo('Europe/Vienna')).date()
    catalog_root,output_dir,cache_dir=map(Path,(catalog_root,output_dir,cache_dir))
    cache_path=cache_dir/'index.json'
    cache=json.loads(cache_path.read_text()) if cache_path.is_file() else {}
    result={};images={}
    for host,row in cache.items():
        body=cached_bytes(row,cache_dir)
        if body is not None:
            result[host]=dict(row);images[row['icon']]=body
        elif row.get('status')=='cached':
            result[host]={'site':row.get('site'),'status':'unavailable','checked_on':row.get('checked_on')}
        else:result[host]=dict(row)
    sites=domains(catalog_root,groups)
    pending=[(host,site) for host,site in sites.items() if host not in result or result[host].get('status')!='cached' or not fresh(result[host],today,refresh_days)]
    stats={'groups':list(groups),'checked_on':today.isoformat(),'requested_domains':len(sites),'reused':len(sites)-len(pending),'downloaded':0,'retained_after_error':0,'unavailable':0}
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for (host,site),download in zip(pending,pool.map(download_icon,pending)):
            if download:
                name=hashlib.sha256(download['data']).hexdigest()[:24]+'.'+download['extension']
                icon='assets/source-logos/'+name;images[icon]=download['data']
                result[host]={'icon':icon,'source':download['source'],'site':site,'status':'cached','checked_on':today.isoformat()}
                stats['downloaded']+=1
            elif result.get(host,{}).get('status')=='cached':
                result[host].update(last_attempt_on=today.isoformat(),refresh_error='No usable favicon returned; retaining previous icon')
                stats['retained_after_error']+=1
            else:
                result[host]={'site':site,'status':'unavailable','checked_on':today.isoformat()}
                stats['unavailable']+=1
    unique={}
    for row in result.values():
        if row.get('status')!='cached':continue
        sha=hashlib.sha256(images[row['icon']]).hexdigest()
        if sha in unique:row['icon']=unique[sha]
        else:unique[sha]=row['icon']
    for icon in {r['icon'] for r in result.values() if r.get('status')=='cached'}:
        atomic_write(output_dir/Path(icon).name,images[icon])
    atomic_write(output_dir/'index.json',(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
    lines=['# Quellenlogos / Favicons','','Öffentliche Favicons der jeweiligen Anbieter, lokal für die Quellenkennzeichnung gespeichert. Die Rechte verbleiben bei den jeweiligen Rechteinhabern.','Neue und fehlende Logos werden gesucht; bestehende Logos standardmäßig nach 30 Tagen erneut geprüft. Bei Abruffehlern bleibt ein vorhandenes Logo erhalten.','','| Domain | Fundstelle | Ergebnis | Letzte erfolgreiche Prüfung / Versuch |','|---|---|---|---|']
    for host,row in sorted(result.items()):
        source=row.get('source') or row.get('site') or 'https://'+host+'/'
        lines.append(f'| {host} | [{host}]({source}) | {row["status"]} | {row.get("checked_on", "unbekannt")} |')
    atomic_write(output_dir/'README.md',('\n'.join(lines)+'\n').encode())
    stats.update(total_domains=len(result),cached_domains=sum(r['status']=='cached' for r in result.values()))
    return stats

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group',choices=('news','authorities','both'),default='both')
    parser.add_argument('--catalog-root',type=Path,default=ROOT)
    parser.add_argument('--output-dir',type=Path,default=DEFAULT_ASSETS)
    parser.add_argument('--cache-dir',type=Path,default=DEFAULT_ASSETS)
    parser.add_argument('--refresh-days',type=int,default=30)
    args=parser.parse_args()
    groups=tuple(CATALOGUES) if args.group=='both' else (args.group,)
    print(json.dumps(refresh_logos(args.catalog_root,args.output_dir,args.cache_dir,groups,args.refresh_days),ensure_ascii=False))
