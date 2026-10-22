#!/usr/bin/env python3
"""Build a deterministic, review-aware production plan from RSS topic candidates.

This does not claim to synthesize or verify facts across articles. No paid APIs.
"""
import argparse, datetime, json, re
from pathlib import Path

def clip(text,limit):
    text=(text or "").strip()
    if len(text)<=limit:return text
    return text[:limit].rsplit(" ",1)[0].rstrip(" ,;:") + "."

def build(analysis,config):
    now=datetime.datetime.now(datetime.timezone.utc)
    max_items=max(1,min(int(config.get("max_items",5)),10))
    limit=max(0,min(int(config.get("max_description_chars",180)),300))
    scenes=config.get("presenter_settings",{}).get("scenes",{})
    mode=scenes.get("intro_mode","avatar")
    if mode not in ("avatar","static"):raise ValueError("Invalid intro mode")
    intro=scenes.get("intro_text","Willkommen bei {title}. Hier sind die Nachrichten.")
    outro=scenes.get("outro_text","Das waren die Schlagzeilen. Quellen und Links finden Sie auf unserer Webseite.")
    if not isinstance(intro,str) or not isinstance(outro,str):raise ValueError("Invalid narration text")
    intro=intro.replace("{title}",str(config.get("title","PersonalNewsHost")))
    if not 1<=len(intro.strip())<=1500 or not 1<=len(outro.strip())<=1500:raise ValueError("Narration text length invalid")
    segments=[{
        "id":"intro","kind":"intro","render_engine":"musetalk" if mode=="avatar" else "ffmpeg",
        "presenter_visible":mode=="avatar",
        "speech_text":intro,
        "sources":[],"review_required":False
    }]
    pending=[]
    for group in analysis["topics"]:
        articles=group["articles"]
        if not articles:continue
        # Candidate matches are NOT fact-merged. Only the first article is
        # narrated, and every candidate is explicitly marked for review.
        lead=articles[0]
        review=len(articles)>1
        if review:pending.append({"topic":group["topic"],"article_count":len(articles),"sources":[{"title":a["title"],"url":a["link"],"publisher":a["source"]} for a in articles]})
        segments.append({
            "id":f"story-{len(segments):02d}","kind":"story",
            "render_engine":"ffmpeg","presenter_visible":False,
            "headline":lead["title"],
            "speech_text":lead["title"].rstrip(".!?")+". "+clip(lead.get("description",""),limit),
            "sources":[{"title":a["title"],"url":a["link"],"publisher":a["source"]} for a in articles],
            "review_required":review,
            "narrated_source_url":lead["link"],
            "narrated_article_count":1,
            "note":"Other sources are similarity candidates, not incorporated into spoken facts" if review else ""
        })
        if len(segments)-1>=max_items:break
    segments.append({
        "id":"outro","kind":"outro","render_engine":"musetalk",
        "presenter_visible":True,
        "speech_text":outro,
        "sources":[],"review_required":False
    })
    return {"schema_version":1,"generated_utc":now.isoformat(),
        "status":"experimental_not_approved_for_publication",
        "method":"One narrated RSS source per topic; candidate source matches require editorial review",
        "rendering":{"parallelizable":True,"presenter_engine":"musetalk","story_engine":"ffmpeg",
                     "publish_enabled":False},
        "segments":segments,"review_queue":pending,
        "feed_errors":analysis.get("feed_errors",[])}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--analysis",default="topic-analysis.json")
    parser.add_argument("--config",default="config.json")
    parser.add_argument("--output",default="broadcast-plan.json")
    args=parser.parse_args()
    analysis=json.loads(Path(args.analysis).read_text(encoding="utf-8"))
    config=json.loads(Path(args.config).read_text(encoding="utf-8"))
    result=build(analysis,config)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Plan: {len(result['segments'])} segments, {len(result['review_queue'])} review candidates; publication disabled")

if __name__=="__main__":main()
