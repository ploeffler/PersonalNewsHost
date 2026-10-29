#!/usr/bin/env python3
"""Stored news -> event groups -> editorial draft -> source-support gate -> selection.

No paid API, remote language model or article scraping. Approval means source
fidelity, never independent confirmation of the underlying real-world facts.
"""
import datetime as dt
from difflib import SequenceMatcher
import hashlib
import html
import json
from pathlib import Path
import re

STOP=set('der die das den dem des ein eine einer einem einen eines und oder aber mit von vom zum zur aus für auf bei nach über gegen wegen durch wurde wurden wird werden ist sind hat haben hatte hätten haben sich nicht mehr neue neuer neues heute jetzt sagt melden meldet berichtet menschen personen'.split())
GENERIC=set('unfall zugunglück erdbeben angriff regierung polizei bericht meldung eilmeldung breaking live'.split())
NUMBERS={'kein':'0','keine':'0','keinen':'0','ein':'1','eine':'1','einer':'1','zwei':'2','drei':'3','vier':'4','fünf':'5','sechs':'6','sieben':'7','acht':'8','neun':'9','zehn':'10','elf':'11','zwölf':'12','dreizehn':'13','vierzehn':'14','fünfzehn':'15','zwanzig':'20'}
SCOPE='stored_source_support'


def prose(value):
    value=re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>',' ',str(value or ''),flags=re.I|re.S)
    value=html.unescape(re.sub(r'<[^>]+>',' ',value))
    value=re.sub(r'!?\[([^\]]+)\]\([^)]*\)',r'\1',value)
    value=re.sub(r'https?://\S+',' ',value)
    value=re.sub(r'\(\s*Bild\b[^)]*\)',' ',value,flags=re.I)
    value=re.sub(r'^([^|.!?]+?)\s*\|\s*([^|.!?]+?)\.\s*[–—-]\s*',lambda m:f'{m[2].strip()} im Bezirk {m[1].strip()}: ',value)
    return re.sub(r'\s+',' ',value).strip()


def words(value):
    return {w for w in re.findall(r'[^\W_]{3,}',prose(value).casefold()) if w not in STOP and w not in NUMBERS}


def places(title):
    matches=re.findall(r'\b(?:in|bei|nahe|vor|near|at|im)\s+(?:(?:der|dem|den|die|das|einem|einer)\s+)?(?:(?:Bezirk|Stadt)\s+)?([A-ZÄÖÜ][\wäöüß-]+(?:\s+[A-ZÄÖÜ][\wäöüß-]+){0,1})',title)
    return {w.casefold() for w in matches if w.casefold() not in GENERIC|STOP|{'krankenhaus','untersuchungshaft'}}


def same_event(first,second):
    a,b=words(first['title']),words(second['title'])
    overlap=len(a&b)
    if overlap<3:return False
    containment=overlap/max(1,min(len(a),len(b)));jaccard=overlap/max(1,len(a|b))
    if containment<.78 or jaccard<.55 or SequenceMatcher(None,first['title'].casefold(),second['title'].casefold()).ratio()<.58:return False
    pa,pb=places(first['title']+'. '+first.get('text','')),places(second['title']+'. '+second.get('text',''))
    return not (pa and pb and not pa&pb)


def age(article):
    first=article.get('first_seen_at') or article.get('published_at') or 0
    return min(first,article['published_at']) if article.get('published_at') else first


def sentence_units(text):
    text=prose(text)
    # Protect dates, decimals and common abbreviations before sentence splitting.
    text=re.sub(r'(?<=\d)\.(?=\d|\s+(?:Jänner|Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember))','\u2024',text)
    text=re.sub(r'\b(?:z\.\s*B|u\.\s*a|d\.\s*h)\.',lambda m:m[0].replace('.','\u2024'),text)
    text=re.sub(r'\b(?:Dr|Prof|bzw|ca|Nr)\.',lambda m:m[0].replace('.','\u2024'),text)
    units=[]
    for part in re.split(r'(?<=[.!?])\s+',text):
        part=part.replace('\u2024','.').strip()
        if not part:continue
        if part[-1] not in '.!?':part+='.'
        units.append(part)
    return units


def publisher(article,feeds):
    from urllib.parse import urlsplit
    host=urlsplit(article.get('url','')).hostname
    if not host and article.get('feed_urls'):host=urlsplit(article['feed_urls'][0]).hostname
    return (host or 'Quelle').removeprefix('www.')


def grouping(articles):
    groups=[]
    for article in sorted(articles,key=lambda a:(-age(a),a['id'])):
        group=next((g for g in groups if all(same_event(article,other) for other in g)),None)
        if group is None:groups.append([article])
        else:group.append(article)
    return groups


def evidence_units(article):
    units=sentence_units(article.get('text',''))
    usable=[s for s in units if 18<=len(s)<=700 and len(words(s))>=2 and not s.endswith('?')
            and s.casefold().rstrip('.!?')!=prose(article['title']).casefold().rstrip('.!?')
            and not re.search(r'^(?:lesen sie|mehr dazu|jetzt abonnieren|hier klicken|read more)\b',s,re.I)]
    return usable


def render_draft(draft,sources):
    headline=draft['headline'] if draft['headline'].endswith(('.', '!', '?')) else draft['headline']+'.'
    if not draft['claims']:return headline
    ids=[draft['headline_source_id']]+[c['source_id'] for c in draft['claims']]
    names=list(dict.fromkeys(sources[sid]['publisher'] for sid in ids))
    credit=('Quelle: ' if len(names)==1 else 'Quellen: ')+', '.join(names)+'.'
    return headline+'\n'+' '.join(c['text'] for c in draft['claims'])+'\n'+credit


def formulate(members,sources,max_sentences=2):
    claims=[];used=[]
    candidates={a['id']:list(evidence_units(a)) for a in members}
    while len(claims)<max_sentences:
        progressed=False
        for article in members:
            units=candidates[article['id']]
            while units:
                sentence=units.pop(0);terms=words(sentence)
                if any(SequenceMatcher(None,sentence.casefold(),old.casefold()).ratio()>=.86 or
                       (terms and len(terms&words(old))/max(1,len(terms|words(old)))>=.82) for old in used):continue
                claims.append({'text':sentence,'source_id':article['id'],'field':'text','quote':sentence})
                used.append(sentence);progressed=True;break
            if len(claims)>=max_sentences:break
        if not progressed:break
    draft={'headline':prose(members[0]['title']),'headline_source_id':members[0]['id'],'claims':claims}
    draft['text']=render_draft(draft,sources)
    return draft


def numeric_conflicts(members):
    pattern=r'\b(\d+(?:[.,]\d+)*|'+ '|'.join(NUMBERS) +r')\s+(?:(?:Menschen|Personen|Männer|Frauen|wurden|werden|sind|schwer|leicht)\s+){0,3}(Verletzt\w*|Tote\w*|getötet|gestorben)\b'
    metrics={}
    for source in members:
        values={}
        for count,unit in re.findall(pattern,source['title']+'. '+source.get('text',''),re.I):
            key='injured' if unit.casefold().startswith('verletzt') else 'dead'
            number=NUMBERS.get(count.casefold(),count)
            if re.fullmatch(r'\d{1,3}(?:\.\d{3})+',number):number=number.replace('.','')
            values.setdefault(key,set()).add(number)
        for key,counts in values.items():
            if len(counts)==1:metrics.setdefault(key,[]).append({'source_id':source['id'],'value':next(iter(counts))})
    return [{'metric':key,'values':values} for key,values in metrics.items()
            if len({v['source_id'] for v in values})>1 and len({v['value'] for v in values})>1]


def wording_conflicts(members):
    negative={'nicht','kein','keine','keinen','keinem','keiner','keines','nie','not','no'}
    uncertain={'möglicherweise','vermutlich','mutmaßlich','angeblich','könnte','könnten','dürfte','dürften','unbestätigt','possibly','allegedly','reportedly'}
    def signature(text):
        tokens=re.findall(r'[^\W_]+',text.casefold())
        base=' '.join(t for t in tokens if t not in negative|uncertain|{'noch','bereits'})
        return base,bool(set(tokens)&negative),bool(set(tokens)&uncertain)
    result=[]
    for index,first in enumerate(members):
        for second in members[index+1:]:
            for a in evidence_units(first):
                sa,na,ua=signature(a)
                for b in evidence_units(second):
                    sb,nb,ub=signature(b)
                    if (na,ua)==(nb,ub) or len(words(a)&words(b))<4:continue
                    if SequenceMatcher(None,sa,sb).ratio()<.88:continue
                    result.append({'kind':'negation' if na!=nb else 'uncertainty',
                                   'source_ids':[first['id'],second['id']],'quotes':[a,b]})
    return result


def verify(draft,members,sources):
    allowed={a['id']:a for a in members};issues=[];checks=[]
    headline_source=allowed.get(draft.get('headline_source_id'))
    if not headline_source or draft.get('headline')!=prose(headline_source['title']):issues.append('unsupported_headline')
    claims=draft.get('claims',[])
    if not claims:issues.append('no_supported_prose')
    for index,claim in enumerate(claims):
        source=allowed.get(claim.get('source_id'))
        supported=bool(source and claim.get('field')=='text' and claim.get('text') in evidence_units(source)
                       and claim.get('quote')==claim.get('text'))
        checks.append({'claim_index':index,'source_id':claim.get('source_id'),'supported':supported,
                       'quote':claim.get('quote')})
        if not supported:issues.append('unsupported_claim:'+str(index))
    try:
        if draft.get('text')!=render_draft(draft,sources):issues.append('unverified_rendered_text')
    except (KeyError,TypeError):issues.append('invalid_source_reference')
    if any(not same_event(a,b) for index,a in enumerate(members) for b in members[index+1:]):issues.append('event_membership_not_supported')
    conflicts=numeric_conflicts(members)
    if conflicts:issues.append('conflicting_source_values')
    wording=wording_conflicts(members)
    if wording:issues.append('conflicting_source_wording')
    conflicts.extend(wording)
    return {'status':'approved' if not issues else 'held','scope':SCOPE,'issues':issues,'claims':checks,
            'conflicts':conflicts,'independent_fact_check':False,'source_independence':'not_assessed'}


def prepare(store,now,max_sentences=2,writer=None):
    eligible=[dict(a) for a in store.get('articles',[]) if a.get('id') and a.get('title')
            and (a.get('published_at') or 0)<=now and now-86400<age(a)<=now]
    excluded=[{'id':a['id'],'title':a['title'],'url':a.get('url',''),'reason':a.get('exclusion_reason','non_news')} for a in eligible if a.get('content_kind')=='non_news']
    active=[a for a in eligible if a.get('content_kind')!='non_news']
    sources={a['id']:{**a,'publisher':publisher(a,store.get('feeds',[]))} for a in active}
    results=[]
    for members in grouping(active):
        gid=hashlib.sha256('|'.join(sorted(a['id'] for a in members)).encode()).hexdigest()[:24]
        draft=(writer or formulate)(members,sources,max_sentences)
        check=verify(draft,members,sources);attempts=[check]
        if check['status']!='approved' and any(i.startswith(('unsupported','unverified','invalid')) for i in check['issues']):
            draft=formulate(members,sources,max_sentences);check=verify(draft,members,sources);attempts.append(check)
        results.append({'id':gid,'member_ids':[a['id'] for a in members],'newest_at':max(age(a) for a in members),
                        'draft':draft,'verification':check,'attempts':[{'status':a['status'],'issues':a['issues']} for a in attempts],'selected':False,
                        'used_source_ids':sorted({draft['headline_source_id']}|{c['source_id'] for c in draft['claims']}) if draft['claims'] else []})
    digest=hashlib.sha256(json.dumps(active,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'version':1,'mode':'preview','generated_at':now,'source_updated_at':store.get('updated_at'),'source_digest':digest,
            'scope':SCOPE,'method':'local_extractive_multi_source','independent_fact_check':False,
            'max_sentences':max_sentences,'sources':sources,'groups':results,'excluded_articles':excluded}


def select(report,limit,selection_config=None):
    try:
        from .news_policy import allowed, source_weight
    except ImportError:
        from news_policy import allowed, source_weight
    config=selection_config or {}
    def entries(group):
        for sid in group['member_ids']:
            member=report['sources'][sid]
            yield (member['title'], member.get('text',''), member.get('url',''), []), next(iter(member.get('feed_urls',[])), '')
    for group in report['groups']:
        group['selection_excluded']=not all(allowed(entry,feed,config) for entry,feed in entries(group))
    ready=sorted((g for g in report['groups'] if g['verification']['status']=='approved' and not g['selection_excluded']),
                 key=lambda g:(-max(source_weight(entry,config) for entry,feed in entries(g)), -g['newest_at'],g['id']))
    selected=[];represented=set()
    for group in ready:
        publishers={report['sources'][sid]['publisher'] for sid in group['member_ids']}
        if publishers-represented:
            selected.append(group);represented.update(publishers)
            if len(selected)>=limit:break
    for group in ready:
        if len(selected)>=limit:break
        if group not in selected:selected.append(group)
    chosen={g['id'] for g in selected}
    for group in report['groups']:group['selected']=group['id'] in chosen
    return selected


def production_plan(path,now,max_sentences=2,limit=5,max_store_age_minutes=30,selection_config=None):
    path=Path(path)
    if not path.is_file():raise RuntimeError('News store missing; run collect_news.py before production')
    store=json.loads(path.read_text(encoding='utf-8'))
    updated=store.get('updated_at',0)
    if not isinstance(updated,(int,float)) or not 0<=now-updated<=max_store_age_minutes*60:
        raise RuntimeError('News store stale; refresh stored messages before production')
    report=prepare(store,now,max_sentences=max(1,min(4,max_sentences)))
    selected=select(report,max(1,min(10,limit)),selection_config)
    report['mode']='production'
    report['selected_ids']=[g['id'] for g in selected]
    output=path.parent/'editorial-report.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not selected:raise RuntimeError('No editorially approved stories; previous publication remains unchanged')
    return report,selected
