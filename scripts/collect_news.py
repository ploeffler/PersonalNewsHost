#!/usr/bin/env python3
"""Persist all RSS messages for 24 hours, with broadcast/update membership."""
import datetime as dt
import email.utils
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ATOM='{http://www.w3.org/2005/Atom}'
RSS1='{http://purl.org/rss/1.0/}'
DC='{http://purl.org/dc/elements/1.1/}'


def clean(text):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',text or ''))).strip()


def identity(url,title,feed=''):
    if url.startswith(('http://','https://')):
        p=urllib.parse.urlsplit(url)
        # Ignore common tracking parameters while keeping article identifiers.
        pairs=[(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.startswith('utm_') and k not in ('ref','fbclid')]
        value=urllib.parse.urlunsplit((p.scheme,p.netloc.lower(),p.path,urllib.parse.urlencode(pairs),''))
    else:value=feed+'|'+title.casefold()
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def timestamp(value):
    if not value:return None
    try:date=email.utils.parsedate_to_datetime(value)
    except (ValueError,TypeError):
        try:date=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:return None
    if date is None:return None
    return date.replace(tzinfo=dt.timezone.utc).timestamp() if date.tzinfo is None else date.timestamp()


def parse_feed(data,url,now):
    root=ET.fromstring(data)
    name=clean(root.findtext('channel/title') or root.findtext(RSS1+'channel/'+RSS1+'title') or root.findtext(ATOM+'title'))
    nodes=root.findall('.//item') or root.findall('.//'+RSS1+'item') or root.findall(ATOM+'entry')
    articles=[]
    for node in nodes:
        ns=ATOM if node.tag==ATOM+'entry' else RSS1 if node.tag==RSS1+'item' else ''
        title=clean(node.findtext(ns+'title'))
        if not title:continue
        text=clean(node.findtext(ns+'description') or node.findtext(ATOM+'summary') or node.findtext(ATOM+'content'))
        link=clean(node.findtext(ns+'link')) if ns!=ATOM else ''
        if ns==ATOM:
            alternate=next((n for n in node.findall(ATOM+'link') if n.get('rel','alternate')=='alternate'),None)
            if alternate is not None:link=alternate.get('href','')
        if not link.startswith(('http://','https://')):link=''
        published=timestamp(node.findtext('pubDate') or node.findtext(DC+'date') or node.findtext(ATOM+'published'))
        articles.append({'id':identity(link,title,url),'title':title,'text':text,'url':link,'published_at':published,
                         'first_seen_at':now,'feed_urls':[url]})
    return name or urllib.parse.urlsplit(url).hostname,articles


def effective_time(article):
    return min(article['published_at'],article['first_seen_at']) if article.get('published_at') else article['first_seen_at']


def merge_articles(previous,incoming,now):
    articles={a['id']:dict(a) for a in previous}
    for item in incoming:
        old=articles.get(item['id'])
        if old:
            times=[t for t in (old.get('published_at'),item.get('published_at')) if t]
            item={**old,**item,'first_seen_at':old['first_seen_at'],
                  'published_at':min(times) if times else None,
                  'feed_urls':sorted(set(old.get('feed_urls',[])+item.get('feed_urls',[])))}
        articles[item['id']]=item
    return sorted((a for a in articles.values() if (a.get('published_at') or 0)<=now and now-86400<effective_time(a)<=now),key=effective_time,reverse=True)


def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def annotate(articles,groups,broadcast,updates,now,historical=()):
    by_id={a['id']:a for a in articles}
    def find(title,url):
        found=next((a for a in list(by_id.values())+list(historical) if (url and a.get('url') and identity(url,title)==identity(a['url'],a['title']))
                     or (not url or not a.get('url')) and a['title'].casefold()==title.casefold()),None)
        if found is not None:
            found=dict(found);by_id[found['id']]=found
        return found
    selected=[];records=[]
    for index,group in enumerate(groups):
        title=group.get('headline','');source=next(iter(group.get('sources',[])),{})
        found=find(title,source.get('url',''))
        if found is None and broadcast.get('created_at'):
            found={'id':identity(source.get('url',''),title),'title':title,'text':clean(source.get('description','')),
                   'url':source.get('url',''),'published_at':None,'first_seen_at':broadcast['created_at'],'feed_urls':[]}
            by_id[found['id']]=found
        if found:
            found['broadcast_id']=broadcast.get('id');found['broadcast_position']=index+1;selected.append(found['id'])
            if not found.get('text'):found['text']=clean(source.get('description',''))
            records.append({k:found.get(k) for k in ('id','title','url','published_at','first_seen_at','feed_urls')})
    for update in updates:
        title=update.get('title','');url=update.get('url','');found=find(title,url)
        if found is None:
            found={'id':identity(url,title),'title':title,'text':update.get('text',title),'url':url,
                   'published_at':update.get('published_at'),'first_seen_at':update['created_at'],'feed_urls':[]}
            by_id[found['id']]=found
        if not found.get('text'):found['text']=update.get('text',title)
        found['short_update_at']=max(found.get('short_update_at',0),update['created_at'])
    return merge_articles([],list(by_id.values()),now),selected,records


def collect(root,fetch=None,now=None):
    root=Path(root);docs=root/'docs';docs.mkdir(exist_ok=True)
    now=now if now is not None else dt.datetime.now(dt.timezone.utc).timestamp()
    config=read(root/'config.json',{});store=read(docs/'news-store.json',{'articles':[],'feeds':[]})
    old_feeds={f['url']:f for f in store.get('feeds',[])};incoming=[];feeds=[]
    for url in dict.fromkeys(config.get('feeds',[])):
        source={'url':url,'name':old_feeds.get(url,{}).get('name',urllib.parse.urlsplit(url).hostname)}
        try:
            if fetch:data=fetch(url)
            else:
                if not url.startswith(('http://','https://')):raise ValueError('Invalid feed URL')
                request=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsHost/1.0 RSS archive'})
                with urllib.request.urlopen(request,timeout=12) as response:data=response.read(2000000)
            source['name'],items=parse_feed(data,url,now);incoming.extend(items);source['last_success_at']=now
        except Exception as exc:
            print('RSS archive source unavailable: '+type(exc).__name__)
        feeds.append(source)
    seen=store.get('seen',{})
    for item in incoming:
        old=seen.get(item['id'],{})
        item['first_seen_at']=old.get('first_seen_at',item['first_seen_at'])
        dates=[t for t in (old.get('published_at'),item.get('published_at')) if t]
        item['published_at']=min(dates) if dates else None
        seen[item['id']]={'first_seen_at':item['first_seen_at'],'published_at':item['published_at'],'last_seen_at':now}
    seen={key:value for key,value in seen.items() if value['last_seen_at']>now-7*86400}
    articles=merge_articles(store.get('articles',[]),incoming,now)
    broadcasts=read(docs/'broadcasts.json',{}).get('broadcasts',[])
    latest=max(broadcasts,key=lambda b:b['created_at'],default={})
    groups=read(docs/'story-groups.json',[])
    updates=read(docs/'short-updates.json',{}).get('updates',[])
    old_latest=store.get('latest_broadcast',{})
    historical=incoming+store.get('articles',[])+(old_latest.get('records',[]) if old_latest.get('id')==latest.get('id') else [])
    articles,selected,records=annotate(articles,groups,latest,updates,now,historical)
    result={'version':1,'updated_at':now,'articles':articles,'feeds':feeds,'seen':seen,
            'latest_broadcast':{'id':latest.get('id'),'created_at':latest.get('created_at'),'article_ids':selected,'records':records}}
    (docs/'news-store.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'RSS archive: {len(articles)} messages, {len(feeds)} feeds')
    return result

if __name__=='__main__':collect(ROOT)
