#!/usr/bin/env python3
"""Build a documented, importable catalogue from direct feed probe results."""
from pathlib import Path
import collections
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RAW=HERE/'feed-research-raw.json'
COUNTRIES={'AT':'Österreich','DE':'Deutschland','CH':'Schweiz','GB':'Großbritannien','US':'USA','CA':'Kanada','NZ':'Neuseeland','AU':'Australien','QA':'Katar','FR':'Frankreich','SG':'Singapur','IN':'Indien','JP':'Japan','HK':'Hongkong'}
CNA={'6511':'Asien','6936':'Wirtschaft','10416':'Singapur','10296':'Sport','6311':'International'}

def topic(r):
    text=(r['url']+' '+r.get('feed_title','')).casefold()
    if r['publisher']=='CNA':
        match=re.search(r'category=(\d+)',r['url'])
        return CNA.get(match[1],'Allgemein') if match else 'Allgemein'
    for label,pattern in [
        ('Meinung',r'opinion|editorial|op-ed|comment|columns|diskurs|kolumn'),
        ('Sport',r'sport|football|fussball|eishockey|hockey|basketball|tennis|ski alpin|motorsport|leichtathletik|cricket|boxing'),
        ('Wirtschaft',r'wirtschaft|business|economy|economics|finance|finanz|money|markets|invest|rss-en-bus|1006/rss|cnbc.com|handelsblatt'),
        ('Technik',r'technolog|technik|digital|web\b|computer|netzwelt|heise|golem|rss-en-tech|1019/rss'),
        ('Wissenschaft',r'wissen|science|forschung|rss-en-sc'),
        ('Gesundheit',r'health|gesundheit'),
        ('Umwelt',r'environment|klima|climate|nachhaltig|natur'),
        ('Kultur',r'kultur|culture|entertainment|music|kunst|film|arts|feuilleton|fm4|oe3'),
        ('International',r'international|world|ausland|africa|asia|europa|europe|americas|middle.?east|rss-en-eu'),
        ('Politik',r'politic|politik|diplomacy'),
    ]:
        if re.search(pattern,text):return label
    if r['publisher'] in ('Kleine Zeitung','Salzburger Nachrichten','Oberösterreichische Nachrichten','Tiroler Tageszeitung'):
        return 'Regional'
    if re.search(r'/inland/regional/|regional|/(steiermark|kaernten|tirol|vorarlberg|wien|noe|ooe|salzburg|burgenland|suedtirol)\.xml|rss/(Muenchen|Bayern)|new york|hong kong|singapore|national\.xml',r['url']+' '+r.get('feed_title',''),re.I):return 'Regional'
    return 'Allgemein'

def identity(r):
    u=r.get('resolved_url',r['url']).rstrip('/')
    if 'rss.dw.com/' in u:u=re.sub(r'/(rdf|atom|xml)/','/feed/',u)
    if 'tagesschau.de/' in u:u=u.replace('~atom.xml','~rss2.xml')
    if r['publisher']=='KURIER' and u.endswith('/layout/xml/rss'):u=u.replace('/layout/xml/rss','/xml/rss')
    return u

def main():
    raw=json.loads(RAW.read_text());entries=[];excluded=[];seen=set()
    for r in raw['feeds']:
        if r['status']!='valid':continue
        declared=r.get('declared_language','').casefold()
        if declared and not declared.startswith(('de','en','ger')):
            excluded.append({'url':r['url'],'reason':'Andere deklarierte Sprache'});continue
        if any(word in (r['url']+' '+r.get('feed_title','')).casefold() for word in ('werbung','newsletter','schedule','recipes','/about-us/','/opinion/cartoon/')):
            excluded.append({'url':r['url'],'reason':'Werbung, Programmschema oder außerhalb des Nachrichtenfokus'});continue
        key=identity(r)
        if key in seen:
            excluded.append({'url':r['url'],'reason':'Alternative Adresse oder XML-Darstellung eines bereits enthaltenen Feeds'});continue
        seen.add(key)
        url=r.get('resolved_url',r['url'])
        notes=[]
        if r['freshness']=='stale':notes.append('Keine Meldung innerhalb der letzten 14 Tage; kann auch selten erscheinendes Angebot sein.')
        if r['freshness']=='future_date':notes.append('Meldungsdatum liegt mehr als zwei Tage in der Zukunft.')
        if r['freshness']=='undated':notes.append('Keine auswertbaren Meldungsdaten; Aktualität unbekannt.')
        if not url.startswith('https://'):notes.append('Weiterleitung auf HTTP; nicht für die HTTPS-Konfiguration geeignet.')
        if r['publisher']=='ABC News Australia':notes.append('Widerspruch: Aktueller Feed technisch abrufbar, offizielle Hilfe erklärt RSS seit 2024 für nicht mehr aktualisiert. Vor Verwendung prüfen.')
        t=topic(r)
        section='economy' if t=='Wirtschaft' else 'local' if t=='Regional' else 'general'
        title=r.get('feed_title') or r['publisher']
        # Some feeds share generic titles; retain a concise URL-specific label.
        if r['publisher']=='CNA':title='CNA – '+t
        if r['publisher']=='BBC News':title='BBC News – '+{'world':'International','business':'Wirtschaft','technology':'Technik','science_and_environment':'Wissenschaft & Umwelt','uk':'Großbritannien'}.get(r['url'].split('/news/')[-1].split('/')[0],'Allgemein')
        if r['publisher']=='tagesschau':
            path=r['url'].split('tagesschau.de/')[-1].replace('/index~rss2.xml','').replace('index~rss2.xml','Startseite')
            title='tagesschau – '+path
        entries.append({'id':hashlib.sha256(url.encode()).hexdigest()[:12],'publisher':r['publisher'],'name':title,'url':url,'language':r['language'],'declared_language':r.get('declared_language',''),'language_basis':'feed_metadata' if declared else 'publisher_language_edition','publisher_country':r['country'],'topic':t,'suggested_section':section,'format':r['format'],'status':'review' if notes else 'verified_recent','checked_at':r['checked_at'],'newest_item_at':r.get('newest_item_at'),'item_count':r['item_count'],'source_page':r['evidence_url'],'evidence_url':r['evidence_url'] if r['discovery']!='candidate' else r['url'],'discovery':r['discovery'],'notes':notes,'enabled_by_default':False})
    entries.sort(key=lambda e:(e['language'],list(COUNTRIES).index(e['publisher_country']),e['publisher'].casefold(),e['topic'],e['name']))
    active=[e for e in entries if e['status']=='verified_recent'];review=[e for e in entries if e['status']=='review']
    org=lambda e: 'Deutsche Welle' if e['publisher'].startswith('DW ') else e['publisher']
    counts={'feeds':len(entries),'verified_recent':len(active),'review':len(review),'publishers':len({org(e) for e in entries}),'publisher_language_editions':len({e['publisher'] for e in entries}),'languages':dict(collections.Counter(e['language'] for e in entries)),'countries':len({e['publisher_country'] for e in entries}),'candidate_urls_checked':len(raw['feeds'])}
    data={'schema_version':1,'researched_on':raw['researched_on'],'scope':'Deutsch- und englischsprachige Nachrichtenfeeds etablierter Anbieter; keine gemessene Reichweitenrangliste, keine Vollständigkeitsbehauptung.','method':raw['method'],'freshness_days':14,'counts':counts,'usage_note':'Erreichbarkeit eines RSS-Feeds ist keine Freigabe zur Veröffentlichung seiner Artikel, Bilder oder Videos. Nutzungsbedingungen des jeweiligen Anbieters beachten.','feeds':entries,'excluded':excluded}
    target=ROOT/'docs/feed-catalog.json';target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    opml=ET.Element('opml',version='2.0');head=ET.SubElement(opml,'head');ET.SubElement(head,'title').text='PersonalNewsHost – recherchierte Nachrichtenfeeds DE/EN'
    body=ET.SubElement(opml,'body')
    for lang,label in [('de','Deutsch'),('en','English')]:
        group=ET.SubElement(body,'outline',text=label,title=label)
        for publisher in dict.fromkeys(e['publisher'] for e in active if e['language']==lang):
            folder=ET.SubElement(group,'outline',text=publisher,title=publisher)
            for e in active:
                if e['publisher']==publisher and e['language']==lang:ET.SubElement(folder,'outline',type='rss',text=e['name'],title=e['name'],xmlUrl=e['url'],htmlUrl=e['source_page'],language=lang)
    ET.indent(opml);ET.ElementTree(opml).write(ROOT/'docs/feed-catalog.opml',encoding='utf-8',xml_declaration=True)
    lines=['# Recherchierte RSS- und Atom-Quellenliste','',f'Stand: **{raw["researched_on"]}**. {counts["feeds"]} Feeds von {counts["publishers"]} Anbietern ({counts["publisher_language_editions"]} Sprachausgaben), {counts["countries"]} Herkunftsländer. Davon {len(active)} technisch geprüft und mit einer Meldung innerhalb von 14 Tagen; {len(review)} zur Nachprüfung.','',f'**Deutsch:** {counts["languages"].get("de",0)} Feeds. **Englisch:** {counts["languages"].get("en",0)} Feeds. Geprüft wurden {len(raw["feeds"])} unterschiedliche Kandidaten-Adressen.','', '**Downloads:** [JSON-Katalog](../feed-catalog.json) · [OPML für Feedreader](../feed-catalog.opml). Die OPML enthält ausschließlich die technisch geprüften, aktuellen Feeds ohne zusätzlichen Prüfhinweis. Es wird keine bestehende Sendungskonfiguration verändert.','', 'Die Auswahl deckt bekannte Nachrichtenportale, öffentlich-rechtliche Angebote und Fachportale ab. „Populär“ ist hier eine qualitative Auswahl; es wurde keine Reichweitenrangliste erhoben. Pro Anbieter wurden zunächst bis zu 32 Kandidaten aus offiziellen Verzeichnissen, HTML-Feedverweisen und bekannten Feed-Adressen geprüft. Anschließend wurden die dokumentierten tagesschau-Ressort- und Regionalfeeds sowie die Sky-News-Ressorts vervollständigt.','', '## Prüfung und Einordnung','', '- Jeder aufgenommene Feed wurde direkt geladen und als RSS 1.0, RSS 2.0 oder Atom geparst. HTTP-Erfolg allein genügte nicht. Weiterleitungsziele und Datum der jüngsten Meldung sind im JSON gespeichert.', '- Sprache beruht auf dem Sprachfeld des Feeds oder der Sprachfassung des Anbieters. Das ist keine automatische Prüfung jedes Artikels; Mischsprachen können vorkommen.', '- Herkunftsland bezeichnet den Anbieter, nicht die gesamte geografische Reichweite. Themen und vorgeschlagene Sendungsbereiche sind heuristische Einordnungen und redaktionell prüfbar.', '- Alternative XML-Darstellungen und erkennbare Weiterleitungs-Dubletten wurden entfernt. Feeds desselben Verlags können weiterhin dieselben Artikel enthalten.', '- 14 Tage sind eine praktische Aktualitätsschwelle, kein Beweis dafür, dass ein seltener erscheinender Feed eingestellt wurde.', '- RSS-Zugang erteilt keine pauschale Erlaubnis zur Übernahme von Artikeln, Bildern oder Videos in eine veröffentlichte Sendung. Zum Beispiel nennen [tagesschau](https://www.tagesschau.de/infoservices/rssfeeds), [The Guardian](https://www.theguardian.com/help/feeds) und [Le Monde](https://www.lemonde.fr/en/about-us/article/2026/03/27/le-monde-rss-feeds_6751860_115.html) eigene Nutzungsbedingungen.','', '## Anbieterübersicht','', '| Anbieter / Sprachausgabe | Sprache | Herkunft | Aktuelle Feeds | Nachprüfung | Offizielle Einstiegsseite |','|---|---|---|---:|---:|---|']
    for publisher in dict.fromkeys(e['publisher'] for e in entries):
        es=[e for e in entries if e['publisher']==publisher];e=es[0];directory=next((d['url'] for d in raw['directories'] if d['publisher']==publisher),e['source_page'])
        lines.append(f'| {publisher} | {e["language"]} | {COUNTRIES[e["publisher_country"]]} | {sum(a["status"]=="verified_recent" for a in es)} | {sum(a["status"]=="review" for a in es)} | [Anbieter]({directory}) |')
    def safe(s):return re.sub(r'\s+',' ',s).replace('|',' / ').replace('[','(').replace(']',')')
    for lang,title in [('de','Deutschsprachige Feeds'),('en','Englischsprachige Feeds')]:
        lines+=['',f'## {title}','','| Anbieter | Feed / Ressort | Thema | Herkunft | RSS / Atom |','|---|---|---|---|---|']
        for e in active:
            if e['language']==lang:lines.append(f'| {e["publisher"]} | {safe(e["name"])} | {e["topic"]} | {e["publisher_country"]} | [Feed]({e["url"]}) |')
    lines+=['','## Technisch lesbar, aber vor Verwendung prüfen','','| Anbieter | Feed | Jüngste Meldung | Grund |','|---|---|---|---|']
    for e in review:lines.append(f'| {e["publisher"]} | [{safe(e["name"])}]({e["url"]}) | {(e["newest_item_at"] or "unbekannt")[:10]} | {" ".join(e["notes"])} |')
    missing=[d['publisher'] for d in raw['directories'] if not any(e['publisher']==d['publisher'] for e in entries)]
    missing_note=('Bei '+', '.join(missing)+' wurde unter den geprüften Kandidaten kein technisch lesbarer Nachrichtenfeed bestätigt. ') if missing else 'Für alle untersuchten Anbieter wurde mindestens ein Feed bestätigt. '
    lines+=['','## Nicht in die reguläre Liste aufgenommen','',missing_note+'Das ist keine Aussage, dass diese Anbieter generell kein RSS mehr anbieten. Fehlermeldungen und geprüfte Adressen stehen im [Prüfprotokoll](../../research/rss/feed-research-raw.json). Auch einzelne leere oder nicht abrufbare Ressortfeeds anderer Anbieter wurden ausgeschlossen.','', 'Für Reuters und AP wurde in dieser Recherche kein öffentlicher Feed technisch bestätigt; veraltete Adressen oder Drittanbieter-Spiegel wurden nicht ergänzt.','', 'ABC Australia: Der Anbieter ist wegen widersprüchlicher Angaben nur zur Nachprüfung vorgesehen. Die [offizielle Hilfe](https://help.abc.net.au/hc/en-us/articles/6147104938383-Why-are-RSS-feeds-no-longer-being-updated) erklärt seit 2024, RSS nicht mehr zu aktualisieren. Den aktuellen technischen Stand dokumentiert das Prüfprotokoll.','', '## Reproduzieren','','Die Quellen und Prüfschritte liegen unter `research/rss/`. `collect.py` lädt Verzeichnisse und prüft die gefundenen Feed-Adressen. `supplement.py` ergänzt die dokumentierten tagesschau-Regionen. `build_catalog.py` erstellt JSON, OPML und diese Übersicht aus dem Prüfprotokoll. Die Skripte benötigen Python 3 und für die Recherche Internetzugang.','']
    (ROOT/'docs/guide/rss-quellenliste.md').write_text('\n'.join(lines))
    print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
