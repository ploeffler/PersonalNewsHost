#!/usr/bin/env python3
"""Collect publisher-linked feeds and probe curated feed candidates; no third-party mirrors."""
import concurrent.futures as cf
import datetime as dt
from zoneinfo import ZoneInfo
import email.utils
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
# publisher | language | country | official directory/homepage | explicit candidate feeds
SEEDS = [
('Fox News','en','US','https://www.foxnews.com/about/rss',['https://moxie.foxnews.com/google-publisher/latest.xml','https://moxie.foxnews.com/google-publisher/world.xml','https://moxie.foxnews.com/google-publisher/politics.xml']),
('The Washington Post','en','US','https://www.washingtonpost.com/discussions/2018/10/12/washington-post-rss-feeds/',['https://feeds.washingtonpost.com/rss/world','https://feeds.washingtonpost.com/rss/business','https://feeds.washingtonpost.com/rss/politics']),
('ORF','de','AT','https://rss.orf.at/',['https://rss.orf.at/news.xml']),
('DER STANDARD','de','AT','https://about.derstandard.at/services/rss-feeds/',['https://www.derstandard.at/rss']),
('Kleine Zeitung','de','AT','https://www.kleinezeitung.at/artikel/5049320/Immer-am-neuesten-Stand_RSS-Feeds-der-Kleinen-Zeitung',['https://www.kleinezeitung.at/rss/steiermark','https://www.kleinezeitung.at/rss/oesterreich','https://www.kleinezeitung.at/rss/wirtschaft','https://www.kleinezeitung.at/rss/kaernten']),
('Kronen Zeitung','de','AT','https://www.krone.at/',['https://api.krone.at/v1/rss/rssfeed-nachrichten.html']),
('KURIER','de','AT','https://kurier.at/',['https://kurier.at/xml/rss']),
('Die Presse','de','AT','https://www.diepresse.com/',['https://www.diepresse.com/rss/home','https://www.diepresse.com/rss/wirtschaft']),
('Salzburger Nachrichten','de','AT','https://www.sn.at/',['https://www.sn.at/xml/rss']),
('Oberösterreichische Nachrichten','de','AT','https://www.nachrichten.at/',['https://www.nachrichten.at/storage/rss/rss/nachrichten.xml']),
('Tiroler Tageszeitung','de','AT','https://www.tt.com/',['https://www.tt.com/rss.xml']),
('tagesschau','de','DE','https://www.tagesschau.de/infoservices/rssfeeds',['https://www.tagesschau.de/index~rss2.xml']),
('ZDFheute','de','DE','https://www.zdfheute.de/',['https://www.zdfheute.de/rss/zdfheute-nachrichten-100.rss','https://www.zdf.de/rss/zdf/nachrichten']),
('DER SPIEGEL','de','DE','https://www.spiegel.de/dienste/rss/',['https://www.spiegel.de/schlagzeilen/index.rss','https://www.spiegel.de/wirtschaft/index.rss','https://www.spiegel.de/politik/index.rss','https://www.spiegel.de/wissenschaft/index.rss']),
('DIE ZEIT','de','DE','https://www.zeit.de/hilfe/hilfe#rss',['https://newsfeed.zeit.de/index','https://newsfeed.zeit.de/wirtschaft/index','https://newsfeed.zeit.de/politik/index','https://newsfeed.zeit.de/wissen/index']),
('Süddeutsche Zeitung','de','DE','https://www.sueddeutsche.de/updates-rss',['https://rss.sueddeutsche.de/rss/Topthemen']),
('FAZ','de','DE','https://www.faz.net/rss/',['https://www.faz.net/rss/aktuell/','https://www.faz.net/rss/aktuell/wirtschaft/']),
('WELT','de','DE','https://www.welt.de/feeds/',['https://www.welt.de/feeds/latest.rss','https://www.welt.de/feeds/section/wirtschaft.rss']),
('n-tv','de','DE','https://www.n-tv.de/mediathek/rss/',['https://www.n-tv.de/rss','https://www.n-tv.de/wirtschaft/rss']),
('FOCUS Online','de','DE','https://www.focus.de/service/rss/',['https://rss.focus.de/fol/XML/rss_folnews.xml']),
('Handelsblatt','de','DE','https://www.handelsblatt.com/',['https://www.handelsblatt.com/contentexport/feed/schlagzeilen']),
('Deutschlandfunk','de','DE','https://www.deutschlandfunk.de/rss',['https://www.deutschlandfunk.de/nachrichten-100.rss']),
('heise online','de','DE','https://www.heise.de/rss/',['https://www.heise.de/rss/heise-atom.xml']),
('Golem','de','DE','https://www.golem.de/sonstiges/rss.html',['https://rss.golem.de/rss.php?feed=RSS2.0']),
('DW Deutsch','de','DE','https://www.dw.com/de/',['https://rss.dw.com/rdf/rss-de-all']),
('SRF','de','CH','https://www.srf.ch/really-simple-syndication-rss-feeds-von-srf',['https://www.srf.ch/news/bnf/rss/1646']),
('NZZ','de','CH','https://www.nzz.ch/',['https://www.nzz.ch/recent.rss','https://www.nzz.ch/wirtschaft.rss','https://www.nzz.ch/international.rss']),
('SWI swissinfo Deutsch','de','CH','https://www.swissinfo.ch/ger/',['https://www.swissinfo.ch/ger/rss']),
('BBC News','en','GB','https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm',['https://feeds.bbci.co.uk/news/rss.xml','https://feeds.bbci.co.uk/news/world/rss.xml','https://feeds.bbci.co.uk/news/business/rss.xml','https://feeds.bbci.co.uk/news/technology/rss.xml','https://feeds.bbci.co.uk/news/science_and_environment/rss.xml','https://feeds.bbci.co.uk/news/uk/rss.xml']),
('The Guardian','en','GB','https://www.theguardian.com/help/feeds',['https://www.theguardian.com/international/rss','https://www.theguardian.com/world/rss','https://www.theguardian.com/business/rss','https://www.theguardian.com/technology/rss','https://www.theguardian.com/science/rss','https://www.theguardian.com/uk-news/rss']),
('Sky News','en','GB','https://news.sky.com/info/rss',['https://feeds.skynews.com/feeds/rss/home.xml']),
('The Independent','en','GB','https://www.independent.co.uk/service/rss-feeds-775086.html',['https://www.independent.co.uk/news/rss','https://www.independent.co.uk/news/business/rss']),
('Financial Times','en','GB','https://www.ft.com/',['https://www.ft.com/rss/home','https://www.ft.com/world?format=rss','https://www.ft.com/companies?format=rss']),
('The Economist','en','GB','https://www.economist.com/',['https://www.economist.com/latest/rss.xml','https://www.economist.com/finance-and-economics/rss.xml']),
('New York Times','en','US','https://www.nytimes.com/rss',['https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml','https://rss.nytimes.com/services/xml/rss/nyt/World.xml','https://rss.nytimes.com/services/xml/rss/nyt/Business.xml','https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml','https://rss.nytimes.com/services/xml/rss/nyt/Science.xml']),
('NPR','en','US','https://www.npr.org/rss/',['https://feeds.npr.org/1001/rss.xml','https://feeds.npr.org/1004/rss.xml','https://feeds.npr.org/1006/rss.xml','https://feeds.npr.org/1019/rss.xml']),
('CNN','en','US','https://edition.cnn.com/services/rss/',['https://rss.cnn.com/rss/edition.rss','https://rss.cnn.com/rss/edition_world.rss','https://rss.cnn.com/rss/money_latest.rss']),
('NBC News','en','US','https://www.nbcnews.com/',['https://feeds.nbcnews.com/nbcnews/public/news','https://feeds.nbcnews.com/nbcnews/public/world']),
('ABC News USA','en','US','https://abcnews.com/Site/page/rss-feeds-3520115',['https://abcnews.go.com/abcnews/topstories']),
('CBS News','en','US','https://www.cbsnews.com/',['https://www.cbsnews.com/latest/rss/main','https://www.cbsnews.com/latest/rss/world']),
('CNBC','en','US','https://www.cnbc.com/rss-feeds/',['https://www.cnbc.com/id/100003114/device/rss/rss.html','https://www.cnbc.com/id/100727362/device/rss/rss.html']),
('PBS NewsHour','en','US','https://www.pbs.org/newshour/',['https://www.pbs.org/newshour/feeds/rss/headlines']),
('CBC','en','CA','https://www.cbc.ca/rss/',['https://www.cbc.ca/webfeed/rss/rss-topstories','https://www.cbc.ca/webfeed/rss/rss-world','https://www.cbc.ca/webfeed/rss/rss-business']),
('Global News','en','CA','https://globalnews.ca/',['https://globalnews.ca/feed/','https://globalnews.ca/world/feed/','https://globalnews.ca/business/feed/']),
('RNZ','en','NZ','https://www.rnz.co.nz/rss',['https://www.rnz.co.nz/rss/national.xml','https://www.rnz.co.nz/rss/world.xml','https://www.rnz.co.nz/rss/business.xml']),
('ABC News Australia','en','AU','https://help.abc.net.au/hc/en-us/articles/6147104938383-Why-are-RSS-feeds-no-longer-being-updated',['https://www.abc.net.au/news/feed/51120/rss.xml']),
('Al Jazeera English','en','QA','https://www.aljazeera.com/',['https://www.aljazeera.com/xml/rss/all.xml']),
('France 24 English','en','FR','https://www.france24.com/en/rss',['https://www.france24.com/en/rss','https://www.france24.com/en/business/rss','https://www.france24.com/en/europe/rss']),
('DW English','en','DE','https://corporate.dw.com/en/rss-feeds/a-68693346',['https://rss.dw.com/rdf/rss-en-all','https://rss.dw.com/rdf/rss-en-bus']),
('Euronews English','en','FR','https://www.euronews.com/rss',['https://www.euronews.com/rss','https://www.euronews.com/rss?level=theme&name=news']),
('Le Monde English','en','FR','https://www.lemonde.fr/en/about-us/article/2026/03/27/le-monde-rss-feeds_6751860_115.html',['https://www.lemonde.fr/en/rss/une.xml','https://www.lemonde.fr/en/international/rss_full.xml','https://www.lemonde.fr/en/economy/rss_full.xml']),
('CNA','en','SG','https://www.channelnewsasia.com/rss',['https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml']),
('The Hindu','en','IN','https://www.thehindu.com/rssfeeds',['https://www.thehindu.com/feeder/default.rss','https://www.thehindu.com/news/international/feeder/default.rss','https://www.thehindu.com/business/feeder/default.rss']),
('The Indian Express','en','IN','https://indianexpress.com/',['https://indianexpress.com/feed/','https://indianexpress.com/section/world/feed/','https://indianexpress.com/section/business/feed/']),
('The Japan Times','en','JP','https://www.japantimes.co.jp/',['https://www.japantimes.co.jp/feed/']),
('South China Morning Post','en','HK','https://www.scmp.com/rss',['https://www.scmp.com/rss/91/feed','https://www.scmp.com/rss/2/feed']),
]

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.anchor=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a': self.anchor=[a.get('href',''),'']
        if tag=='link' and ('rss' in a.get('type','') or 'atom' in a.get('type','')):
            self.links.append((a.get('href',''),a.get('title',''),True))
    def handle_data(self,data):
        if self.anchor: self.anchor[1]+=data
    def handle_endtag(self, tag):
        if tag=='a' and self.anchor:
            u,label=self.anchor
            if re.search(r'rss|\.xml(?:$|\?)|\.atom|\.rdf|/feed(?:/|$)|format=rss',u,re.I): self.links.append((u,label.strip(),False))
            self.anchor=None

def read(url):
    req=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsHost RSS directory research/1.0','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8'})
    with urllib.request.urlopen(req,timeout=12) as r: return r.geturl(),r.headers.get_content_type(),r.read(2_000_000)

def directory(seed):
    name,lang,country,page,explicit=seed
    rows=[{'publisher':name,'language':lang,'country':country,'url':u,'evidence_url':page,'discovery':'candidate','label':''} for u in explicit]
    try:
        final,mime,body=read(page)
        parser=Links(); parser.feed(body.decode('utf-8',errors='replace'))
        for plain in re.findall(r'https?://[^\s<>\"\']+', html.unescape(body.decode('utf-8',errors='replace'))):
            if re.search(r'(?:rss2?|atom|rdf|rss_full)\.xml(?:$|\?)', plain):
                parser.links.append((plain, '', False))
        for u,label,auto in parser.links:
            u=urllib.parse.urljoin(final,html.unescape(u)).split('#')[0]
            if u.startswith('http://'): u='https://'+u[7:]
            if not u.startswith('https://'): continue
            # Keep publisher feeds only; no social links, trackers or aggregators.
            host=urllib.parse.urlparse(u).hostname or ''
            pagehost=urllib.parse.urlparse(final).hostname or ''
            if host.split('.')[-2:] != pagehost.split('.')[-2:] and not (name=='ORF' and host.endswith('orf.at')) and not (name=='Sky News' and host=='feeds.skynews.com'): continue
            if u==page or any(x in u for x in ('podcast','kommentar','comments','abo.xml')): continue
            rows.append({'publisher':name,'language':lang,'country':country,'url':u,'evidence_url':final,'discovery':'publisher_link','label':label})
        return rows,{'publisher':name,'url':page,'status':'retrieved'}
    except Exception as e: return rows,{'publisher':name,'url':page,'status':'unavailable','error':str(e)[:180]}

def local(tag): return tag.rsplit('}',1)[-1]
def text(node,name):
    return next((' '.join(''.join(c.itertext()).split()) for c in node if local(c.tag)==name),'')
def date(value):
    if not value:return None
    try:
        result=email.utils.parsedate_to_datetime(value)
    except (ValueError,TypeError,OverflowError):
        try: result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:return None
    if result.tzinfo is None:result=result.replace(tzinfo=dt.timezone.utc)
    return result.astimezone(dt.timezone.utc)

def probe(row):
    row=dict(row); row['checked_at']=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    try:
        final,mime,body=read(row['url']);row['resolved_url']=final
        root=ET.fromstring(body)
        if local(root.tag) not in ('rss','RDF','feed'):raise ValueError('Response is not RSS/RDF/Atom')
        channel=next((x for x in root if local(x.tag)=='channel'),root)
        entries=[x for x in root.iter() if local(x.tag) in ('item','entry')]
        row.update(format='atom' if local(root.tag)=='feed' else 'rss1' if local(root.tag)=='RDF' else 'rss2',feed_title=text(channel,'title'),declared_language=text(channel,'language') or root.get('{http://www.w3.org/XML/1998/namespace}lang',''),item_count=len(entries))
        dates=[date(text(e,'pubDate') or text(e,'published') or text(e,'updated') or text(e,'date')) for e in entries]; dates=[d for d in dates if d]
        newest=max(dates) if dates else None
        row['newest_item_at']=newest.isoformat() if newest else None
        row['status']='valid' if entries else 'empty'
        if newest:
            age=(dt.datetime.now(dt.timezone.utc)-newest).total_seconds()/86400
            row['freshness']='future_date' if age < -2 else 'recent' if age<=14 else 'stale'
            row['age_days']=round(age,1)
        else:row['freshness']='undated'
    except Exception as e:row.update(status='unavailable',error=str(e)[:200])
    return row

def main():
    with cf.ThreadPoolExecutor(max_workers=8) as pool: collected=list(pool.map(directory,SEEDS))
    rows=[];seen=set()
    for candidates,_ in collected:
        # Broad coverage, with up to 32 feeds per publisher, avoiding hundreds of narrow subfeeds.
        for row in candidates:
            if row['url'] in seen:continue
            if sum(r['publisher']==row['publisher'] for r in rows)>=32:break
            seen.add(row['url']);rows.append(row)
    print(f'Probing {len(rows)} feeds from {len(SEEDS)} publishers',flush=True)
    with cf.ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(probe,rows))
    data={'researched_on':dt.datetime.now(ZoneInfo('Europe/Vienna')).date().isoformat(),'method':'Official publisher directories, HTML feed discovery and curated candidates, followed by direct XML parsing. Language is publisher/feed-edition metadata, not automatic language detection. Freshness threshold: 14 days. No audience rankings measured.','directories':[d for _,d in collected],'feeds':results}
    (OUT/'feed-research-raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'feeds':len(results),'valid':sum(r['status']=='valid' for r in results),'publishers_valid':len({r['publisher'] for r in results if r['status']=='valid'}),'failed_publishers':[s[0] for s in SEEDS if not any(r['publisher']==s[0] and r['status']=='valid' for r in results)]},ensure_ascii=False))
if __name__=='__main__':main()
