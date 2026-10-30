import sys,json,concurrent.futures as cf
from pathlib import Path
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from collect import SEEDS,directory,probe
p=root/'feed-research-raw.json';x=json.loads(p.read_text());seen={r['url'] for r in x['feeds']};new=[]
for seed in SEEDS:
 if seed[0] not in ('Sky News','tagesschau'):continue
 rows,_=directory(seed)
 for r in rows:
  if '[' in r['url'] or r['url'] in seen:continue
  seen.add(r['url']);new.append(r)
for region in ('badenwuerttemberg','bayern','berlin','brandenburg','bremen','hamburg','hessen','mecklenburgvorpommern','niedersachsen','nordrheinwestfalen','rheinlandpfalz','saarland','sachsen','sachsenanhalt','schleswigholstein','thueringen'):
 u=f'https://www.tagesschau.de/inland/regional/{region}/index~rss2.xml'
 if u not in seen:new.append({'publisher':'tagesschau','language':'de','country':'DE','url':u,'evidence_url':'https://www.tagesschau.de/infoservices/rssfeeds','discovery':'documented_template','label':region})
with cf.ThreadPoolExecutor(max_workers=8) as pool:x['feeds']+=list(pool.map(probe,new))
p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print('Additional candidates:',len(new),'valid:',sum(r['status']=='valid' for r in x['feeds']))
