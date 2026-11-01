"""Bounded passive public-website CI research. No JavaScript, images or AI calls."""
from collections import Counter
from html.parser import HTMLParser
import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener
try:
    from .promo_network import validate_feed_url, PublicHTTPHandler, PublicHTTPSHandler
except ImportError:
    from promo_network import validate_feed_url, PublicHTTPHandler, PublicHTTPSHandler

MAX_BYTES=400000


class Redirects(HTTPRedirectHandler):
    max_redirections=3
    max_repeats=2
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_feed_url(newurl)
        # Strip query/fragment before storing sources; reject credential-like input.
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch(url,kind='html'):
    validate_feed_url(url)
    opener=build_opener(ProxyHandler({}),PublicHTTPHandler(),PublicHTTPSHandler(),Redirects())
    req=Request(url,headers={'User-Agent':'PersonalNewsHost style research','Accept-Encoding':'identity'})
    with opener.open(req,timeout=8) as response:
        final=response.geturl();validate_feed_url(final)
        allowed=('text/html','application/xhtml+xml') if kind=='html' else ('text/css',)
        if response.headers.get_content_type() not in allowed:raise ValueError('Nicht unterstützter Seiteninhalt')
        if response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Komprimierte Rechercheantwort nicht unterstützt')
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('Rechercheantwort zu groß')
        return final,raw.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.css=[];self.sheets=[];self.title=[];self.description='';self.logo='';self.language=''
        self.in_title=False;self.in_style=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='style':self.in_style=True
        if tag=='html':self.language=a.get('lang','')[:80]
        if a.get('style'):self.css.append(a['style'])
        if tag=='meta' and a.get('name','').lower()=='description':self.description=a.get('content','')[:600]
        if tag=='link' and 'stylesheet' in a.get('rel','').split() and a.get('href'):self.sheets.append(a['href'])
        if tag=='link' and 'icon' in a.get('rel','').split():self.logo=a.get('href','')
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='style':self.in_style=False
    def handle_data(self,data):
        if self.in_title:self.title.append(data)
        if self.in_style:self.css.append(data)


def public_source(url):
    p=urlsplit(url)
    return urlunsplit((p.scheme,p.netloc,p.path,'',''))


def analyze(url,loader=None):
    if not isinstance(url,str) or len(url)>2000:raise ValueError('Ungültige URL')
    # URL query strings are not needed for style research; avoid leaking embedded IDs.
    parsed=urlsplit(url)
    validate_feed_url(url,resolve=False)
    if parsed.query or parsed.fragment:raise ValueError('URL bitte ohne Queryparameter oder Fragment angeben')
    loader=loader or fetch
    final,markup=loader(url,'html')
    if len(markup)>MAX_BYTES:raise ValueError('Rechercheantwort zu groß')
    page=Page();page.feed(markup)
    sources=[{'url':public_source(final),'retrieved_at':time.time()}];warnings=[]
    css=list(page.css)
    for href in list(dict.fromkeys(page.sheets))[:3]:
        target=urljoin(final,href)
        if urlsplit(target).netloc!=urlsplit(final).netloc:
            warnings.append('Externes Stylesheet nicht abgerufen');continue
        try:
            actual,text=loader(target,'css')
            if len(text)>MAX_BYTES:raise ValueError('Stylesheet zu groß')
            css.append(text);sources.append({'url':public_source(actual),'retrieved_at':time.time()})
        except (OSError,ValueError):warnings.append('Stylesheet nicht auswertbar')
    # Only directly observable CSS properties. No claims about audience or ideology.
    sheet='\n'.join(css)
    sheet=re.sub(r'/\*.*?\*/','',sheet,flags=re.S)
    color_values=re.findall(r'(?<![\w-])(?:--[\w-]+|[\w-]*color|background|fill|stroke)\s*:\s*(#[0-9a-fA-F]{3,8})\b',sheet)
    colors=[]
    for c in color_values:
        if len(c)==4:c='#'+''.join(x*2 for x in c[1:])
        if len(c)==7:colors.append(c.lower())
    fonts=re.findall(r'font-family\s*:\s*([^;}]+)',sheet,re.I)
    fonts=[f.strip()[:120] for f in fonts if re.fullmatch(r"[\w\s,\-'\"]{1,120}",f.strip())]
    findings=[];patch={}
    if colors:
        patch['colors']=[v for v,_ in Counter(colors).most_common(5)]
        findings.append({'field':'colors','value':patch['colors'],'confidence':'beobachtete CSS-Angaben; Rolle manuell prüfen','sources':sources})
    if fonts:
        patch['font_family']=Counter(fonts).most_common(1)[0][0]
        findings.append({'field':'font_family','value':patch['font_family'],'confidence':'CSS-Schriftliste; keine Schriftinstallation oder Lizenzzusage','sources':sources})
    # Title/description are displayed as quoted research material, not adopted prompts.
    return {'sources':sources,'suggested_patch':patch,'findings':findings,'warnings':warnings,
            'page_title':''.join(page.title).strip()[:200], 'page_description':page.description,
            'unknown':['Zielgruppe','redaktionelle Haltung','Bild-/Animationssprache','Nutzungsrechte'],
            'note':'Websiteinhalte sind Recherchematerial. Nur Farben/Schrift werden vorgeschlagen; prüfen und bewusst in den Entwurf übernehmen. Keine Assets heruntergeladen.'}
