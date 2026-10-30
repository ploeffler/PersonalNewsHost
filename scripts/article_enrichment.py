"""Bounded public-article enrichment before editorial drafting and source checks."""
import datetime as dt
from difflib import SequenceMatcher
from html.parser import HTMLParser
import hashlib
import ipaddress
import json
import re
import shutil
import socket
import subprocess
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES=2_000_000
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
BODY_CLASSES={'article-text','article-body','article__body','article-content','story-body','story-content','entry-content'}


def plain(text):
    return re.sub(r'\s+',' ',text or '').strip()


def url_allowed(url,resolve=False):
    try:p=urllib.parse.urlsplit(url)
    except ValueError:return False
    if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:return False
    host=p.hostname.lower()
    if host=='localhost' or host.endswith(('.localhost','.local')):return False
    try:
        if not ipaddress.ip_address(host).is_global:return False
    except ValueError:pass
    if resolve:
        try:
            addresses={item[4][0] for item in socket.getaddrinfo(host,p.port or (443 if p.scheme=='https' else 80))}
            if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):return False
        except OSError:return False
    return True


def same_site(first,second):
    a=(urllib.parse.urlsplit(first).hostname or '').removeprefix('www.')
    b=(urllib.parse.urlsplit(second).hostname or '').removeprefix('www.')
    return a==b or (a=='orf.at' or a.endswith('.orf.at')) and (b=='orf.at' or b.endswith('.orf.at'))


class Redirects(urllib.request.HTTPRedirectHandler):
    max_redirections=5
    max_repeats=2
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not same_site(req.full_url,newurl) or not url_allowed(newurl,resolve=True):
            raise ValueError('Unapproved article redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def download(url):
    if not url_allowed(url,resolve=True):raise ValueError('Article URL is not public HTTP(S)')
    req=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsHost/1.0 article enrichment','Accept':'text/html,application/xhtml+xml'})
    with urllib.request.build_opener(Redirects()).open(req,timeout=10) as response:
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError('Article exceeds byte limit')
        charset=response.headers.get_content_charset() or 'utf-8'
        return {'body':body.decode(charset,errors='replace'),'final_url':response.geturl(),
                'status':response.status,'content_type':response.headers.get_content_type()}


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.p=None;self.paragraphs={'orf':[],'body':[],'article':[]};self.title=[];self.h1=[];self.meta={};self.canonical='';self.script=None;self.json_ld=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=set(a.get('class','').split());keys=(a.get('id','')+' '+' '.join(classes)).lower()
        skip=tag in {'nav','footer','aside','script','style'} or bool(re.search(r'consent|privacywall|paywall|cookie-banner|login',keys))
        inherited=any(f['skip'] for f in self.stack)
        scopes=set().union(*(f['scopes'] for f in self.stack)) if self.stack else set()
        if 'story-story' in classes:scopes.add('orf')
        if classes&BODY_CLASSES or a.get('itemprop')=='articleBody':scopes.add('body')
        if tag=='article':scopes.add('article')
        if tag=='meta':self.meta[a.get('property',a.get('name','')).lower()]=a.get('content','')
        if tag=='link' and 'canonical' in a.get('rel','').split():self.canonical=a.get('href','')
        if tag=='script' and a.get('type','').lower()=='application/ld+json':self.script=[]
        if tag not in VOID:self.stack.append({'tag':tag,'skip':skip or inherited,'scopes':scopes})
        if tag=='p' and scopes and not (skip or inherited):self.p={'parts':[],'scopes':scopes}
    def handle_data(self,data):
        if self.script is not None:self.script.append(data)
        if any(f['tag']=='title' for f in self.stack):self.title.append(data)
        if any(f['tag']=='h1' for f in self.stack) and not any(f['skip'] for f in self.stack):self.h1.append(data)
        if self.p is not None and not any(f['skip'] for f in self.stack):self.p['parts'].append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.script is not None:
            try:self.json_ld.append(json.loads(''.join(self.script)))
            except ValueError:pass
            self.script=None
        if tag=='p' and self.p is not None:
            value=plain(''.join(self.p['parts']))
            if value and not re.search(r'^(?:Bitte akzeptieren|Um diesen Artikel|Sie entscheiden darüber|Willkommen bei DER STANDARD)',value,re.I):
                for scope in self.p['scopes']:self.paragraphs[scope].append(value)
            self.p=None
        for index in range(len(self.stack)-1,-1,-1):
            if self.stack[index]['tag']==tag:self.stack=self.stack[:index];break


def records(value):
    if isinstance(value,dict):
        kind=value.get('@type',[]);kind=[kind] if isinstance(kind,str) else kind
        if any(k in ('Article','NewsArticle','ReportageNewsArticle') for k in kind):yield value
        for item in value.values():yield from records(item)
    elif isinstance(value,list):
        for item in value:yield from records(item)


def title_matches(expected,actual):
    a=re.findall(r'[^\W_]+',expected.casefold());b=re.findall(r'[^\W_]+',actual.casefold())
    if not a or not b:return False
    if ' '.join(a) in ' '.join(b):return True
    return len(set(a)&set(b))/max(1,len(set(a)))>=.8 and SequenceMatcher(None,' '.join(a),' '.join(b)).ratio()>=.65


def usable(title,text):
    try:
        from scripts.editorial_pipeline import evidence_units
    except ModuleNotFoundError:
        from editorial_pipeline import evidence_units
    return len(text)>=160 and bool(evidence_units({'title':title,'text':text}))


def extract(title,url,document):
    final=document.get('final_url',url)
    if not same_site(url,final) or not url_allowed(final):return {'status':'redirect_rejected','resolved_url':final}
    if re.search(r'/(?:consent|login|signin|paywall)(?:/|\b)',urllib.parse.urlsplit(final).path,re.I):return {'status':'consent_or_login','resolved_url':final}
    if document.get('status',200)!=200:return {'status':'http_error','resolved_url':final,'http_status':document.get('status')}
    if document.get('content_type','').split(';')[0] not in ('text/html','application/xhtml+xml'):return {'status':'not_html','resolved_url':final}
    parser=Document();parser.feed(document['body'])
    canonical=urllib.parse.urljoin(final,parser.canonical) if parser.canonical else final
    if not same_site(final,canonical) or not url_allowed(canonical):return {'status':'canonical_rejected','resolved_url':final}
    articles=[r for data in parser.json_ld for r in records(data)]
    if any(r.get('isAccessibleForFree') in (False,'false') for r in articles):return {'status':'paywall','resolved_url':final,'canonical_url':canonical}
    headlines=[plain(parser.meta.get('og:title','')),plain(''.join(parser.h1)),plain(''.join(parser.title))]
    matched=next((h for h in headlines if title_matches(title,h)),None)
    if not matched:return {'status':'title_mismatch','page_title':next((h for h in headlines if h),'')}
    candidates=[]
    if (urllib.parse.urlsplit(final).hostname or '').endswith('orf.at'):
        candidates.append(('orf_story_story','\n\n'.join(dict.fromkeys(parser.paragraphs['orf']))))
    for item in articles:
        if isinstance(item.get('articleBody'),str) and title_matches(title,str(item.get('headline') or matched)):
            candidates.append(('json_ld_article_body',plain(re.sub(r'<[^>]+>',' ',item['articleBody']))))
    candidates.extend((method,'\n\n'.join(dict.fromkeys(parser.paragraphs[key]))) for key,method in [('body','article_body_dom'),('article','article_dom')])
    for method,text in candidates:
        text=text[:24000].strip()
        if usable(title,text):return {'status':'success','text':text,'method':method,'page_title':matched,'canonical_url':canonical,'resolved_url':final}
    return {'status':'no_article_text','page_title':matched,'canonical_url':canonical,'resolved_url':final}


def rdrr_fallback(title,url):
    if not shutil.which('rdrr'):return None
    try:
        result=subprocess.run(['rdrr',url,'--format','json','--no-history','--strict'],capture_output=True,text=True,timeout=20,check=True)
        value=json.loads(result.stdout)
        if value.get('extractionEmpty'):return None
        try:
            from scripts.generate import spoken_prose
        except ModuleNotFoundError:
            from generate import spoken_prose
        body=spoken_prose(value.get('content',''))[:24000]
        return body if usable(title,body) else None
    except (OSError,subprocess.SubprocessError,ValueError):return None


def fingerprint(article):
    return hashlib.sha256((article['title']+'\0'+article.get('rss_text','')+'\0'+str(article.get('rss_revision_at',''))).encode()).hexdigest()


def enrich_articles(articles,now,settings=None,fetch=None):
    settings=settings or {};fetcher=fetch or download
    budget=max(0,min(60,int(settings.get('max_fetches_per_run',24))))
    for article in articles:
        article.setdefault('rss_text',article.get('text',''))
        if re.search(r'^(?:Smart\s+)?Sudoku(?:\s+(?:sehr\s+)?(?:leicht|mittel|schwierig|einfach|schwer)|\s+\d)|^Kreuzworträtsel\s+(?:vom|\d)',article['title'],re.I):
            article.update(content_kind='non_news',exclusion_reason='puzzle');continue
        article['content_kind']='news';article.pop('exclusion_reason',None)
        # Prefer the saved RSS text if it is already a substantial source.
        if usable(article['title'],article['rss_text']):
            article.update(text=article['rss_text'],text_origin='rss');article.pop('article_text',None);article.pop('article_fetch',None)
    if settings.get('enabled',True) is False:return articles
    ordered=sorted(articles,key=lambda a:(bool(a.get('rss_text','').strip()),not (urllib.parse.urlsplit(a.get('url','')).hostname or '').endswith('orf.at'),-(a.get('published_at') or a.get('first_seen_at',now))))
    for article in ordered:
        if article.get('content_kind')=='non_news':continue
        rss=article['rss_text'];title=article['title'];url=article.get('url','')
        if usable(title,rss) or not url_allowed(url):continue
        previous=article.get('article_fetch',{});version=fingerprint(article);same=previous.get('rss_fingerprint')==version
        cached=article.get('article_text','') if same else ''
        if cached and usable(title,cached):
            article.update(text=cached,text_origin='linked_article')
            if now-previous.get('fetched_at',0)<6*3600:continue
        else:article.update(text=rss,text_origin='rss');article.pop('article_text',None)
        retry=6*3600 if previous.get('status') in ('consent_or_login','paywall') else 1800
        if same and not cached and previous.get('status')!='deferred' and now-previous.get('last_attempt_at',0)<retry:continue
        if budget<=0:
            article['article_fetch']={**previous,'status':'deferred' if not cached else previous.get('status'),'rss_fingerprint':version}
            continue
        budget-=1
        try:
            document=fetcher(url);result=extract(title,url,document)
            if result['status']=='no_article_text':
                body=rdrr_fallback(title,document.get('final_url',url)) if fetch is None else None
                if body:result={**result,'status':'success','text':body,'method':'rdrr'}
        except urllib.error.HTTPError as exc:result={'status':'http_error','http_status':exc.code}
        except Exception as exc:result={'status':'fetch_error','error_type':type(exc).__name__}
        metadata={k:v for k,v in result.items() if k!='text'}
        metadata.update(requested_url=url,last_attempt_at=now,rss_fingerprint=version)
        if result['status']=='success':
            body=result['text'];metadata.update(fetched_at=now,text_sha256=hashlib.sha256(body.encode()).hexdigest())
            article.update(text=body,article_text=body,text_origin='linked_article')
        elif cached:
            metadata={**previous,'last_attempt_at':now,'last_error':result['status']}
        article['article_fetch']=metadata
    return articles
