#!/usr/bin/env python3
"""Conservative RSS topic clustering, independent of the production publisher."""
import argparse, html, json, re, unicodedata, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

STOP=set("der die das den dem des ein eine einer einem eines und oder zu zur zum im in am an auf aus bei mit von für nach über unter als ist sind wird werden wurde wurden hat haben auch noch schon mehr neue neuen neuer neues nun jetzt heute gestern aktuell gegen wegen durch um vor vom ins beim ihr ihre ihren seinen seine seinem dieser diese dieses dessen deren so wie was warum wer wo wenn dass nicht kein keine erste ersten zwei drei".split())

def clean(value):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",value or ""))).strip()

def tokens(text):
    value=unicodedata.normalize("NFKC",clean(text)).casefold().replace("ß","ss")
    return {w for w in re.findall(r"[a-zäöü0-9]{3,}",value) if w not in STOP}

def similarity(a,b):
    x,y=tokens(a["title"]),tokens(b["title"])
    if not x or not y:return 0.0
    if x==y:return 1.0
    common=x&y
    if len(common)<2:return 0.0
    return len(common)/len(x|y)+min(.12,.04*sum(len(w)>=7 for w in common))

def parse_feed(data,url):
    root=ET.fromstring(data)
    atom="{http://www.w3.org/2005/Atom}"
    nodes=root.findall(".//item") or root.findall(".//"+atom+"entry")
    output=[]
    for node in nodes[:30]:
        title=clean(node.findtext("title") or node.findtext(atom+"title"))
        desc=clean(node.findtext("description") or node.findtext(atom+"summary") or node.findtext(atom+"content"))
        link=clean(node.findtext("link"))
        if not link:
            element=node.find(atom+"link")
            if element is not None:link=element.get("href","")
        if title:output.append({"title":title,"description":desc,"link":link,"source":urlparse(url).netloc})
    return output

def group_items(items,threshold=.50):
    groups=[]
    for item in items:
        match=None;best=threshold
        for group in groups:
            # Complete-link matching avoids broad-topic chaining.
            score=min(similarity(item,existing) for existing in group["articles"])
            if score>=best:match=group;best=score
        if match is None:groups.append({"topic":item["title"],"articles":[item]})
        else:match["articles"].append(item)
    for group in groups:
        group["sources"]=sorted({x["source"] for x in group["articles"]})
        group["article_count"]=len(group["articles"])
        group["multi_source"]=len(group["sources"])>1
        group["review_required"]=group["article_count"]>1
    return groups

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",default="config.json")
    parser.add_argument("--output",default="topic-analysis.json")
    parser.add_argument("--threshold",type=float,default=.50)
    args=parser.parse_args()
    config=json.loads(Path(args.config).read_text(encoding="utf-8"))
    items=[];errors=[]
    for url in config["feeds"]:
        try:
            if urlparse(url).scheme not in ("http","https"):raise ValueError("Invalid RSS URL")
            req=urllib.request.Request(url,headers={"User-Agent":"PersonalNewsHost/0.5-topic-analysis"})
            with urllib.request.urlopen(req,timeout=15) as response:data=response.read(2_000_000)
            items.extend(parse_feed(data,url))
        except Exception as exc:errors.append({"feed":url,"error":str(exc)})
    if not items:raise SystemExit("No RSS entries; cannot analyze")
    groups=group_items(items,args.threshold)
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"total_articles":len(items),
      "topic_count":len(groups),"multi_article_topics":sum(g["article_count"]>1 for g in groups),
      "multi_source_topics":sum(g["multi_source"] for g in groups),
      "feed_errors":errors,"topics":groups,
      "method":"Conservative headline similarity; potential matches require review; source descriptions are not automatically blended"}
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f'{len(items)} articles -> {len(groups)} topics; {report["multi_source_topics"]} cross-source candidates')

if __name__=="__main__":main()
