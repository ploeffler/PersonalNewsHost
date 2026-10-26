#!/usr/bin/env python3
"""Conservative RSS topic clustering, independent of the production publisher."""
import argparse, html, json, re, unicodedata, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.research_language import event_candidate, normalize_language
except ModuleNotFoundError:
    from research_language import event_candidate, normalize_language

STOP=set("der die das den dem des ein eine einer einem eines und oder zu zur zum im in am an auf aus bei mit von für nach über unter als ist sind wird werden wurde wurden hat haben auch noch schon mehr neue neuen neuer neues nun jetzt heute gestern aktuell gegen wegen durch um vor vom ins beim ihr ihre ihren seinen seine seinem dieser diese dieses dessen deren so wie was warum wer wo wenn dass nicht kein keine erste ersten zwei drei".split())

def clean(value):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",value or ""))).strip()

def tokens(text):
    value=unicodedata.normalize("NFKC",clean(text)).casefold().replace("ß","ss")
    return {w for w in re.findall(r"[a-zäöü0-9]{3,}",value) if w not in STOP}

def similarity(a,b):
    """Conservative candidate scoring using headlines plus supporting descriptions."""
    x,y=tokens(a["title"]),tokens(b["title"])
    if not x or not y:return 0.0
    if x==y:return 1.0
    overlap=x&y
    title_score=len(overlap)/len(x|y)
    # The descriptions help distinguish events when titles use different wording.
    dx,dy=tokens(a.get("description","")),tokens(b.get("description",""))
    evidence=(x|dx)&(y|dy)
    description_score=len(evidence)/max(1,min(len(x|dx),len(y|dy)))
    # The following score is only for review candidates, not factual merging.
    if len(overlap)>=2:
        return max(title_score+.04*sum(len(w)>=7 for w in overlap),
                   min(.72, .20+description_score))
    # Strong shared proper-name / technical-term signal in a title plus
    # supporting description; a lone generic keyword must not suffice.
    if len(overlap)==1 and next(iter(overlap)) in {"php","kiew"}:
        return min(.65,.28+description_score)
    return 0.0

def parse_feed(data,url):
    root=ET.fromstring(data)
    atom="{http://www.w3.org/2005/Atom}"
    nodes=root.findall(".//item") or root.findall(".//"+atom+"entry")
    output=[]
    feed_lang = root.findtext(".//language") or root.findtext(".//"+atom+"feed/"+atom+"language") or ""
    if not feed_lang:
        feed_lang = root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "")
    language = normalize_language(feed_lang, default="unknown")
    for node in nodes[:30]:
        title=clean(node.findtext("title") or node.findtext(atom+"title"))
        desc=clean(node.findtext("description") or node.findtext(atom+"summary") or node.findtext(atom+"content"))
        link=clean(node.findtext("link"))
        if not link:
            element=node.find(atom+"link")
            if element is not None:link=element.get("href","")
        if title:output.append({"title":title,"description":desc,"link":link,"source":urlparse(url).netloc,"language":language})
    return output

def group_items(items,threshold=.38):
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

def bilingual_candidates(items, threshold=0.3):
    """Cross-language review candidates only; never merge or claim verification."""
    results = []
    for i, first in enumerate(items):
        for second in items[i + 1:]:
            if first.get("language") not in ("de", "en") or second.get("language") not in ("de", "en"):
                continue
            if first["language"] == second["language"]:
                continue
            if first.get("source") == second.get("source"):
                continue
            evidence = event_candidate(first["title"], second["title"])
            if not evidence["candidate"] or evidence["score"] < threshold:
                continue
            results.append({
                "first": {"title": first["title"], "url": first.get("link", ""),
                          "source": first.get("source", ""), "language": first["language"]},
                "second": {"title": second["title"], "url": second.get("link", ""),
                           "source": second.get("source", ""), "language": second["language"]},
                "score": evidence["score"], "shared_terms": evidence["shared_terms"],
                "review_required": True, "independent_verification": False
            })
    return sorted(results, key=lambda result: -result["score"])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",default="config.json")
    parser.add_argument("--output",default="topic-analysis.json")
    parser.add_argument("--threshold",type=float,default=.38)
    parser.add_argument("--bilingual-output",default="",help="Optional JSON report for DE/EN review candidates")
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
    bilingual = bilingual_candidates(items)
    if args.bilingual_output:
        report_path = Path(args.bilingual_output)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_count": len(bilingual), "candidates": bilingual,
            "note": "Review candidates only; not evidence of independent factual verification"},
            ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"total_articles":len(items),
      "topic_count":len(groups),"multi_article_topics":sum(g["article_count"]>1 for g in groups),
      "multi_source_topics":sum(g["multi_source"] for g in groups),
      "feed_errors":errors,"topics":groups,
      "bilingual_candidate_count":len(bilingual), "bilingual_candidates":bilingual,
      "method":"Conservative headline similarity; potential matches require review; source descriptions are not automatically blended"}
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f'{len(items)} articles -> {len(groups)} topics; {report["multi_source_topics"]} cross-source candidates')

if __name__=="__main__":main()
